from dataclasses import dataclass, field
from enum import StrEnum, auto
import math
import re
from typing import Generator
from dataclasses_json import dataclass_json, config
import yaml
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RECIPE_DIR = DATA_DIR / "recipes"
NUM_COLORS = 8
INGR_PATTERN_STRING = r"\$([^$]+)\$"
TIMER_PATTERN_STRING = r"!(([^!]+) *(second|minute|hour)s?)!"
BOLD_PATTERN_STRING = r"\*\*([^*]+)\*\*"
INGR_PATTERN = re.compile(INGR_PATTERN_STRING)
INGR_UID_PATTERN = re.compile(r"\s*\[([^\]]+)\]$")
TIMER_PATTERN = re.compile(TIMER_PATTERN_STRING)
BOLD_PATTERN = re.compile(BOLD_PATTERN_STRING)
TASK_SPLIT_PATTERN = re.compile(
    f"({INGR_PATTERN_STRING}|{TIMER_PATTERN_STRING}|{BOLD_PATTERN_STRING})"
)
INGR_LINK_PATTERN = re.compile(r"~([^~]+)~")


class Mise(StrEnum):
    NONE = auto()
    START = auto()
    END = auto()


@dataclass_json
@dataclass
class Ingredient:
    uid: str = ""
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


@dataclass_json
@dataclass
class Step:
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
    color_index: int = 0
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
class Recipe:
    id: str
    name: str
    categories: set[str]
    icon: str
    ingredient_groups: list[IngredientGroup] = field(default_factory=list)
    ingredient_map: dict[str, Ingredient] = field(default_factory=dict)
    steps: list[Step] = field(default_factory=list)

    def all_ingredients(self) -> Generator[Ingredient]:
        for g in self.ingredient_groups:
            yield from g.ingredients


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
) -> dict[str, Category]:
    print("Reloading recipes")
    categories = {}
    recipes = {}
    for r in list_recipe_files(recipe_dir):
        try:
            recipe = load_recipe_from_file(r)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error loading {r}: {e}")
            continue

        recipes[recipe.id] = recipe

        for cat in recipe.categories:
            cat_id = cat.lower()
            if cat_id not in categories:
                categories[cat_id] = Category(name=cat)

            categories[cat_id].recipes.append(recipe)

    resolve_links(recipes)

    return categories, recipes


def resolve_links(recipes: dict[str, Recipe]):
    for r in recipes.values():
        for i in r.all_ingredients():
            if not i.linked_recipe_id:
                continue

            linked_recipe = recipes.get(i.linked_recipe_id)
            if not linked_recipe:
                print(
                    f"WARN: Ingredient link {i.linked_recipe_id} in {r.id} is not valid"
                )

            i.text = linked_recipe.name


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
    text, uid = sub_and_keep_match(
        INGR_UID_PATTERN,
        lambda _: "",
        ingr_line,
    )

    text, name = sub_and_keep_match(
        INGR_PATTERN,
        clean_ingr_name,
        text,
    )

    text, link_id = sub_and_keep_match(
        INGR_LINK_PATTERN,
        clean_ingr_name,
        text,
    )

    return Ingredient(
        uid=uid,
        name=name,
        text=text,
        linked_recipe_id=link_id,
    )


def handle_steps(step_lines, recipe: Recipe):

    def handle_special_part_match(match, step):
        ingr_match = INGR_PATTERN.match(match)
        if ingr_match:
            ingr_part = handle_task_ingredient(ingr_match)
            ingr_index_in_step = add_ingredient_to_step(ingr_part, step)
            ingr_part.color_index = ingr_index_in_step % NUM_COLORS
            task.parts.append(ingr_part)
            return

        timer_match = TIMER_PATTERN.match(match)
        if timer_match:
            task.parts.append(handle_task_timer(timer_match))
            return

        bold_match = BOLD_PATTERN.match(match)
        if bold_match:
            task.parts.append(
                TextPart(
                    text=bold_match.group(1),
                    style="bold",
                )
            )

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
            print(
                f"WARNING: Task ingredient '{ingr_part.name}' is not part of recipe ({recipe.name} step {len(recipe.steps)})"
            )
            ingr = Ingredient(
                name=ingr_part.name,
                text=ingr_part.text,
            )
        step.ingredients.append(ingr)

        return len(step.ingredients) - 1

    for step_line in step_lines:
        step = Step()
        recipe.steps.append(step)
        for task_line in step_line["tasks"]:
            task = Task()

            k = 0
            for m in re.finditer(TASK_SPLIT_PATTERN, task_line):
                if m.start() > k:
                    task.parts.append(TextPart(text=task_line[k : m.start()]))

                handle_special_part_match(m.group(), step)

                k = m.end()

            if k < len(task_line) - 1:
                task.parts.append(TextPart(text=task_line[k:]))

            step.tasks.append(task)


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
