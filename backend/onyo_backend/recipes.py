from dataclasses import dataclass, field
from enum import StrEnum, auto
import math
import re
import traceback
from typing import Generator
from dataclasses_json import dataclass_json, config
import yaml
from functools import lru_cache, partial
from pathlib import Path
import rich

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RECIPE_DIR = DATA_DIR / "recipes"
NUM_COLORS = 8
INGR_PATTERN_STRING = r"\$([^$]+)\$"
TIMER_PATTERN_STRING = r"!(([^!]+) *(second|minute|hour)s?)!"
BOLD_PATTERN_STRING = r"\*\*([^*]+)\*\*"
INGR_PATTERN = re.compile(INGR_PATTERN_STRING)
TIMER_PATTERN = re.compile(TIMER_PATTERN_STRING)
BOLD_PATTERN = re.compile(BOLD_PATTERN_STRING)
TASK_SPLIT_PATTERN = re.compile(
    f"({INGR_PATTERN_STRING}|{TIMER_PATTERN_STRING}|{BOLD_PATTERN_STRING})"
)
NOTE_SPLIT_PATTERN = re.compile(f"({BOLD_PATTERN_STRING})")
INGR_LINK_PATTERN = re.compile(r"~([^~]+)~")


class Mise(StrEnum):
    NONE = auto()
    START = auto()
    END = auto()


@dataclass_json
@dataclass
class Ingredient:
    name: str = ""
    text: str = ""
    mise: Mise = field(
        default=Mise.NONE,
        metadata=config(
            encoder=str,
            decoder=Mise,
        ),
    )
    linked_recipe_id: str = ""


@dataclass_json
@dataclass
class Timer:
    title: str
    seconds: int


@dataclass_json
@dataclass
class Task:
    parts: list = field(default_factory=list)

    def ingredient_indices(self):
        return [p.ingr_index_in_step for p in self.parts if p.type == "ingredient"]


@dataclass_json
@dataclass
class Step:
    title: str = ""
    tasks: list[Task] = field(default_factory=list)
    ingredients: list[Ingredient] = field(default_factory=list)
    timers: list[Timer] = field(default_factory=list)


@dataclass_json
@dataclass
class TextPart:
    text: str
    style: str = ""
    type: str = "text"


@dataclass_json
@dataclass
class IngredientPart:
    name: str
    text: str
    ingr_index_in_step: int = 0
    type: str = "ingredient"


@dataclass_json
@dataclass
class TimerPart:
    text: str
    seconds: int
    type: str = "timer"


@dataclass_json
@dataclass
class IngredientGroup:
    title: str
    ingredients: list[Ingredient] = field(default_factory=list)


@dataclass_json
@dataclass
class Note:
    parts: list = field(default_factory=list)


@dataclass_json
@dataclass
class Warning:
    msg: str
    extra_context: str = ""


@dataclass_json
@dataclass
class Recipe:
    id: str
    name: str
    categories: set[str]
    icon: str
    ingredient_groups: list[IngredientGroup] = field(default_factory=list)
    ingredient_map: dict[str, Ingredient] = field(default_factory=dict)
    steps: list[Step] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    warnings: list[Warning] = field(default_factory=list)

    def all_ingredients(self) -> Generator[Ingredient, None, None]:
        for g in self.ingredient_groups:
            yield from g.ingredients

    def searchable_ingredients(self) -> set[str]:
        def sanitize(text: str):
            return re.sub(
                r"([0-9./ ]+\s*(dl|ml|l|g|kg|tb?sp|cups?)\s*)|(^[0-9-+]+ )", "", text
            ).lower()

        search = {sanitize(ingr.text) for ingr in self.all_ingredients()}
        return search

    def add_warning(self, msg: str, extra_context: str = ""):
        self.warnings.append(Warning(msg, extra_context))


@dataclass_json
@dataclass
class Category:
    name: str
    recipes: list[Recipe] = field(default_factory=list)


def list_recipes():
    lmod = get_last_mod(RECIPE_DIR)
    return load_recipes(RECIPE_DIR, lmod)


def get_last_mod(recipe_dir):
    lmod = recipe_dir.lstat().st_mtime
    for r in list_recipe_files(recipe_dir):
        lmod = max(lmod, r.lstat().st_mtime)
    return lmod


def list_recipe_files(recipe_dir):
    return recipe_dir.glob("*.yaml")


def load_recipe_yaml(recipe_id):
    path = RECIPE_DIR / f"{recipe_id}.yaml"
    with open(path, "r", encoding="utf8") as file:
        return file.read()


def save_recipe_yaml(recipe_id, recipe_yaml):
    path = RECIPE_DIR / f"{recipe_id}.yaml"
    with open(path, "w", encoding="utf8") as file:
        file.write(recipe_yaml)


@lru_cache(maxsize=1)
def load_recipes(
    recipe_dir,
    lmod,  # pylint: disable=unused-argument
) -> tuple[dict[str, Category], dict[str, Recipe]]:
    print("Reloading recipes")
    errors = []
    categories, recipes = load_recipes_uncached(recipe_dir, errors)
    print_errors(errors)
    print_warnings(recipes.values())
    return categories, recipes


def load_recipes_uncached(recipe_dir, errors: list[str]):
    categories = {}
    recipes = {}
    for r in list_recipe_files(recipe_dir):
        try:
            recipe = load_recipe_from_file(r)
        except Exception as e:  # pylint: disable=broad-exception-caught
            err = f"Error loading {r}: {e}" + "\n" + traceback.format_exc()
            errors.append(err)
            continue

        recipes[recipe.id] = recipe

        for cat in recipe.categories:
            cat_id = cat.lower()
            if cat_id not in categories:
                categories[cat_id] = Category(name=cat)

            categories[cat_id].recipes.append(recipe)

    resolve_links(recipes)

    return categories, recipes


def print_errors(errors: list[str]):
    for e in errors:
        rich.print(f"[red]ERROR[/red]: {e}")


def print_warnings(recipes: list[Recipe]):
    for r in recipes:
        path = RECIPE_DIR / f"{r.id}.yaml"
        for w in r.warnings:
            ctx = f"[cyan]{path}[/cyan]"
            if w.extra_context:
                ctx += f", {w.extra_context}"
            rich.print(f"[orange3]WARNING[/orange3]: {w.msg} ({ctx})")


def resolve_links(recipes: dict[str, Recipe]):
    for r in recipes.values():
        for i in r.all_ingredients():
            if not i.linked_recipe_id:
                continue

            linked_recipe = recipes.get(i.linked_recipe_id)
            if linked_recipe:
                i.text = linked_recipe.name
            else:
                r.add_warning(f"Ingredient link {i.linked_recipe_id} is not valid")


def load_recipe_from_file(path) -> Recipe:
    with open(path, "r", encoding="utf8") as file:
        data = yaml.safe_load(file)

    return load_recipe(
        data,
        path.name.replace(".yaml", "").lower(),
    )


def load_recipe(data, recipe_id) -> Recipe:
    raw_categories = data["category"]
    if isinstance(raw_categories, str):
        categories = {raw_categories}
    else:
        categories = set(raw_categories)

    recipe = Recipe(
        id=recipe_id,
        name=data["name"],
        categories=categories,
        icon=data.get("icon", ""),
    )

    handle_ingredients(data["ingredients"], recipe)
    handle_steps(data.get("steps", []), recipe)
    handle_notes(data.get("notes", []), recipe)
    validate(recipe)

    return recipe


def handle_ingredients(ingredient_lines, recipe: Recipe):
    last_line = None
    group = IngredientGroup(title="")

    def add_current_group():
        if group.ingredients:
            recipe.ingredient_groups.append(group)

    for ingr_line in ingredient_lines:
        if ingr_line.startswith("=") and ingr_line.endswith("="):
            add_current_group()
            group = IngredientGroup(title=ingr_line[1:-1].strip())
        elif ingr_line == ")":
            group.ingredients[-1].mise = Mise.END
        elif ingr_line != "(":
            ingr = handle_ingredient(ingr_line)
            if last_line == "(":
                ingr.mise = Mise.START

            group.ingredients.append(ingr)

            if ingr.name:
                recipe.ingredient_map[ingr.name] = ingr

        last_line = ingr_line

    add_current_group()


def handle_ingredient(ingr_line) -> Ingredient:
    text, name = sub_and_keep_match(
        INGR_PATTERN,
        clean_ingr_name,
        ingr_line,
    )

    text, link_id = sub_and_keep_match(
        INGR_LINK_PATTERN,
        clean_ingr_name,
        text,
    )

    return Ingredient(
        name=name,
        text=text,
        linked_recipe_id=None if link_id is None else link_id.lower(),
    )


def handle_steps(step_lines, recipe: Recipe):

    def handle_special_part(match, step):
        ingr_match = INGR_PATTERN.match(match)
        if ingr_match:
            ingr_part = handle_task_ingredient(ingr_match)
            ingr_index_in_step = add_ingredient_to_step(ingr_part, step)
            ingr_part.ingr_index_in_step = ingr_index_in_step
            return ingr_part

        timer_match = TIMER_PATTERN.match(match)
        if timer_match:
            return handle_task_timer(timer_match)

        return handle_formatted_text_part(match)

    def handle_task_ingredient(m):
        ingr_name = m.group(1)
        return IngredientPart(
            name=ingr_name,
            text=clean_ingr_name(ingr_name),
        )

    def handle_task_timer(m):
        factors = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
        }

        text = m.group(1)
        amount = float(m.group(2))
        unit = m.group(3)
        seconds = math.floor(factors[unit] * amount)
        return TimerPart(text=text, seconds=seconds)

    def add_ingredient_to_step(ingr_part: IngredientPart, step: Step):
        ind = index_of(step.ingredients, lambda ingr: ingr.name == ingr_part.name)
        if ind >= 0:
            return ind

        ingr = recipe.ingredient_map.get(ingr_part.name)
        if ingr is None:
            recipe.add_warning(
                f"Task ingredient '{ingr_part.name}' is not part of recipe",
                extra_context=f"step {len(recipe.steps)}, task {len(step.tasks) + 1}",
            )
            ingr = Ingredient(
                name=ingr_part.name,
                text=ingr_part.text,
            )

        step.ingredients.append(ingr)

        return len(step.ingredients) - 1

    for step_line in step_lines:
        step = Step(title=step_line.get("title", ""))
        recipe.steps.append(step)
        for task_line in step_line["tasks"]:
            task = Task(
                parts=handle_parts(
                    task_line,
                    TASK_SPLIT_PATTERN,
                    partial(handle_special_part, step=step),
                )
            )

            step.tasks.append(task)


def handle_notes(note_lines: list[str], recipe: Recipe):
    recipe.notes = [
        Note(
            parts=handle_parts(
                line,
                NOTE_SPLIT_PATTERN,
                handle_formatted_text_part,
            )
        )
        for line in note_lines
    ]


def handle_parts(line: str, special_part_pattern, handle_special_part):
    parts = []
    k = 0
    for m in re.finditer(special_part_pattern, line):
        if m.start() > k:
            parts.append(TextPart(text=line[k : m.start()]))

        special_part = handle_special_part(m.group())
        if special_part:
            parts.append(special_part)

        k = m.end()

    if k < len(line) - 1:
        parts.append(TextPart(text=line[k:]))

    return parts


def handle_formatted_text_part(match):
    bold_match = BOLD_PATTERN.match(match)
    if bold_match:
        return TextPart(
            text=bold_match.group(1),
            style="bold",
        )
    return None


def validate(recipe: Recipe):
    # Note some validations/warnings are handled during parsing already.
    validate_mise_grouping_in_steps(recipe)


def validate_mise_grouping_in_steps(recipe: Recipe):
    HINT = "Hint: maybe you are referencing the wrong numbered ingredient (e.g. $cream:1$ instead of $cream:2$)"
    for i, step in enumerate(recipe.steps):
        in_mise_group = False
        for ingr in step.ingredients:
            extra_ctx = f"step {i + 1}, ingredient {ingr.name}"
            if ingr.mise == Mise.START:
                if in_mise_group:
                    recipe.add_warning(
                        f"Nested mise group. {HINT}",
                        extra_context=extra_ctx,
                    )
                in_mise_group = True
            if ingr.mise == Mise.END:
                if not in_mise_group:
                    recipe.add_warning(
                        f"Ending unstarted mise group. {HINT}",
                        extra_context=extra_ctx,
                    )
                in_mise_group = False

        if in_mise_group:
            recipe.add_warning(
                f"Mise group not ended. {HINT}",
                extra_context=f"step {i + 1}",
            )


def clean_ingr_name(ingr_name):
    return re.sub(r":[0-9]+$", "", ingr_name)


def sub_and_keep_match(pattern, repl_func, line):
    match = None

    def handle_match(m):
        nonlocal match
        match = m.group(1)
        return repl_func(match)

    replaced = re.sub(pattern, handle_match, line)
    return replaced, match


def index_of(lst, predicate):
    return next((i for i, e in enumerate(lst) if predicate(e)), -1)


def normalize_ingr_name_for_shopping(name: str):
    ALIASES = {
        "egg yolk": "egg",
        "bay leave": "bay leaf",
        "potatoe": "potato",
        "tomatoe": "tomato",
    }
    name = name.lower()
    # Remove numeric suffix
    name = re.sub(r":[0-9]+$", "", name)
    # Remove plural 's' (doesn't always make correct words, but good enough)
    name = re.sub(r"s$", "", name)
    # Normalize aliases
    name = ALIASES.get(name, name)
    return name


def normalize_for_recipe_id(name: str):
    normalized = name.replace("'s", "s")
    normalized = re.sub(r"([^a-zA-Z0-9])+", " ", normalized).title().replace(" ", "")
    return normalized[0].lower() + normalized[1:]


def create_empty_recipe(name: str, recipe_dir=RECIPE_DIR) -> str:
    recipe_id = normalize_for_recipe_id(name)
    spaghetti_emoji = "\U0001f35d"
    with open(recipe_dir / f"{recipe_id}.yaml", "w", encoding="utf8") as file:
        file.write(
            f"""\
---
name: {name}
icon: {spaghetti_emoji}
category: [Meal]
ingredients:
- dummy ingredient
steps:
- title: dummy step
  tasks:
  - dummy task

# notes:
#  - dummy notes
"""
        )

    return recipe_id
