from dataclasses import dataclass, field
from enum import Enum, auto
import math
import re
import yaml
from functools import lru_cache
from pathlib import Path

RECIPE_DIR = Path(__file__).parent.parent.parent / "recipes"
NUM_COLORS = 8


class Mise(Enum):
    NONE = auto()
    START = auto()
    END = auto()


@dataclass
class Ingredient:
    name: str = ""
    text: str = ""
    mise: Mise = Mise.NONE


@dataclass
class Timer:
    title: str
    seconds: int


@dataclass
class Step:
    tasks: list[str] = field(default_factory=list)
    ingredients: list[Ingredient] = field(default_factory=list)
    timers: list[Timer] = field(default_factory=list)


@dataclass
class Recipe:
    id: str
    name: str
    categories: set[str]
    icon: str
    ingredients: list[Ingredient] = field(default_factory=list)
    ingredient_map: dict[str, Ingredient] = field(default_factory=dict)
    steps: list[Step] = field(default_factory=list)


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


@lru_cache(maxsize=1)
def load_recipes(recipe_dir, lmod) -> dict[str, Category]:
    print("Reloading recipes")
    categories = {}
    for r in list_recipe_files(recipe_dir):
        try:
            recipe = load_recipe(r)
        except Exception as e:
            print(f"Error loading {r}: {e}")
            continue

        for cat in recipe.categories:
            cat_id = cat.lower()
            if cat_id not in categories:
                categories[cat_id] = Category(name=cat)

            categories[cat_id].recipes.append(recipe)

    return categories


def load_recipe(path) -> Recipe:
    with open(path, "r", encoding="utf8") as file:
        data = yaml.safe_load(file)

    raw_categories = data["category"]
    if isinstance(raw_categories, str):
        categories = {raw_categories}
    else:
        categories = set(raw_categories)

    recipe = Recipe(
        id=path.name.replace(".yaml", "").lower(),
        name=data["name"],
        categories=categories,
        icon=data.get("icon", ""),
    )

    def handle_ingr_name(m):
        ingr = recipe.ingredients[-1]
        ingr.name = m.group(1)
        return ingr.name

    last_line = None
    for ingr_line in data["ingredients"]:
        if ingr_line == ")":
            recipe.ingredients[-1].mise = Mise.END
        elif ingr_line != "(":
            ingr = Ingredient(mise=Mise.START if last_line == "(" else Mise.NONE)
            recipe.ingredients.append(ingr)
            ingr.text = re.sub(r"@([^@]+)@", handle_ingr_name, ingr_line)
            if ingr.name:
                recipe.ingredient_map[ingr.name] = ingr

        last_line = ingr_line

    ingr_indexes = {}

    def handle_task_ingr_name(m):
        step = recipe.steps[-1]

        ingr_name = m.group(1)
        seen = ingr_name in ingr_indexes
        ingr_index = ingr_indexes.get(ingr_name, len(step.ingredients))
        ingr_indexes[ingr_name] = ingr_index
        color_index = ingr_index % NUM_COLORS
        ingr = recipe.ingredient_map.get(
            ingr_name,
            Ingredient(
                name=ingr_name,
                text=ingr_name,
            ),
        )

        if not seen:
            step.ingredients.append(ingr)

        return f'<span class="ingr{color_index}">{ingr_name}</span>'

    def handle_timer(m):
        factors = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
        }

        full = m.group(1)
        amount = float(m.group(2))
        unit = m.group(3)
        seconds = math.floor(factors[unit] * amount)
        return f'<span class="timer"><a href="launchtimer://?seconds={seconds}&title={recipe.name}">{full}</a></span>'

    for step_data in data.get("steps", []):
        step = Step()
        recipe.steps.append(step)
        for task_line in step_data["tasks"]:
            clean_task = re.sub(r"@([^@]+)@", handle_task_ingr_name, task_line)
            clean_task = re.sub(
                r"!(([^!]+) *(second|minute|hour)s?)!", handle_timer, clean_task
            )
            clean_task = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", clean_task)
            step.tasks.append(clean_task)

    return recipe
