from collections import defaultdict
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from functools import lru_cache

from onyo_backend.recipes import (
    DATA_DIR,
    Ingredient,
    Recipe,
    list_recipes,
    normalize_ingr_name_for_shopping,
)

UNKNOWN = "unknown"
IGNORE = "ignore"
SHOPPING_LINKS_PATH = DATA_DIR / "shopping_links.yaml"


@dataclass
class ShoppingIngredient:
    name: str
    link: str
    used_in_recipes: list[str] = field(default_factory=list)


@dataclass_json
@dataclass
class ShoppingListItem:
    text: str
    link: str


@dataclass_json
@dataclass
class ShoppingList:
    items: list[ShoppingListItem] = field(default_factory=list)


def get_shopping_ingredients():
    lmod = SHOPPING_LINKS_PATH.lstat().st_mtime
    return load_shopping_ingredients_if_changed(SHOPPING_LINKS_PATH, lmod)


@lru_cache(maxsize=1)
def load_shopping_ingredients_if_changed(
    shopping_links_file,
    lmod,
):
    return load_shopping_ingredients(shopping_links_file)


def load_shopping_ingredients(path) -> dict[str, ShoppingIngredient]:
    ingredients = {}
    with open(path, "r", encoding="utf8") as file:
        for line in file:
            if line.lstrip().startswith("#"):
                continue

            ingr, link = [p.strip() for p in line.split(":", maxsplit=1)]
            ingredients[ingr] = ShoppingIngredient(name=ingr, link=link)
    return ingredients


def save_shopping_ingredients(
    ingredients: dict[str, ShoppingIngredient], path, origins
):
    with open(path, "w", encoding="utf8") as file:
        for ingr in sorted(ingredients.values(), key=lambda i: i.name):
            file.write(f"{ingr.name}: {ingr.link}\n")
            if origins:
                for r in sorted(ingr.used_in_recipes):
                    file.write(f"  # file://./recipes/{r}.yaml\n")


def update_shopping_links(origins: bool):
    _, recipes = list_recipes()
    shopping_ingredients_in_file = load_shopping_ingredients(SHOPPING_LINKS_PATH)
    shopping_ingredients_in_recipes = collect_ingredients_from_recipes(recipes)
    shopping_ingredients_merged = merge_shopping_links(
        shopping_ingredients_in_file,
        shopping_ingredients_in_recipes,
    )

    special_counts = defaultdict(int)
    for ingr in shopping_ingredients_merged.values():
        if ingr.link in {IGNORE, UNKNOWN}:
            special_counts[ingr.link] += 1

    print(f"{len(shopping_ingredients_merged)} ingredients")
    for lnk, cnt in special_counts.items():
        print(f"{cnt} ingredients using '{lnk}'")

    if special_counts[UNKNOWN] > 0:
        print(
            f"WARN: There are {special_counts[UNKNOWN]} ingredients with unknown shopping link. Hint: use '{IGNORE}' if link doesn't make sense."
        )

    save_shopping_ingredients(
        shopping_ingredients_merged,
        SHOPPING_LINKS_PATH,
        origins,
    )

    print(f"Updated {SHOPPING_LINKS_PATH}")


def collect_ingredients_from_recipes(recipes: dict[str, Recipe]):
    def ingredients_with_name():
        for r in recipes.values():
            for i in r.all_ingredients():
                if i.name is not None:
                    yield i, r

    shopping_ingredients = {}
    for ingr, recipe in ingredients_with_name():
        name = normalize_ingr_name_for_shopping(ingr.name)
        shopping_ingr = shopping_ingredients.get(name)
        if not shopping_ingr:
            shopping_ingr = ShoppingIngredient(name=name, link=UNKNOWN)
            shopping_ingredients[name] = shopping_ingr
        shopping_ingr.used_in_recipes.append(recipe.id)

    return shopping_ingredients


def merge_shopping_links(shopping_ingredients_in_file, shopping_ingredients_in_recipes):
    merged = {}
    for name, ingr in shopping_ingredients_in_file.items():
        if name in shopping_ingredients_in_recipes:
            ingr.used_in_recipes = shopping_ingredients_in_recipes[name].used_in_recipes
        else:
            print(f"WARN: {name} is no longer used in any recipe")
        merged[name] = ingr

    for name, ingr in shopping_ingredients_in_recipes.items():
        if name not in merged:
            print(f"NEW INGREDIENT: {name}")
            merged[name] = ingr

    return merged


def assemble_shopping_list(
    recipe: Recipe,
    shopping_ingredients: dict[str, ShoppingIngredient],
) -> ShoppingList:
    def to_item(ingr: Ingredient):
        link: str = UNKNOWN
        if ingr.name:
            shopping_name = normalize_ingr_name_for_shopping(ingr.name)
            shopping_ingr = shopping_ingredients.get(shopping_name)
            link = shopping_ingr.link if shopping_ingr else UNKNOWN

        return ShoppingListItem(
            text=ingr.text,
            link=link if link not in {IGNORE, UNKNOWN} else "",
        )

    items = sorted(
        [to_item(ingr) for ingr in recipe.all_ingredients()],
        key=lambda i: 0 if i.link else 1,
    )

    return ShoppingList(items=items)
