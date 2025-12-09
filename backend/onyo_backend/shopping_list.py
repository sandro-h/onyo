from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import yaml
from functools import lru_cache

from onyo_backend.recipes import DATA_DIR, Ingredient, Recipe

SHOPPING_LINKS_FILE = DATA_DIR / "shopping_links.yaml"


@dataclass_json
@dataclass
class ShoppingLink:
    link: str


@dataclass_json
@dataclass
class ShoppingLinks:
    links: dict[str, ShoppingLink] = field(default_factory=dict)


@dataclass_json
@dataclass
class ShoppingListItem:
    text: str
    link: str


@dataclass_json
@dataclass
class ShoppingList:
    items: list[ShoppingListItem] = field(default_factory=list)


def get_shopping_links():
    lmod = SHOPPING_LINKS_FILE.lstat().st_mtime
    return load_shopping_links(SHOPPING_LINKS_FILE, lmod)


@lru_cache(maxsize=1)
def load_shopping_links(
    shopping_links_file,
    lmod,  # pylint: disable=unused-argument
):
    with open(shopping_links_file, "r", encoding="utf8") as file:
        data = yaml.safe_load(file)

    return ShoppingLinks.from_dict(data)


def assemble_shopping_list(
    recipe: Recipe,
    shopping_links: ShoppingLinks,
) -> ShoppingList:
    def to_item(ingr: Ingredient):
        link: ShoppingLink = None
        if ingr.uid:
            link = shopping_links.links.get(ingr.uid)
            if not link:
                print(f"WARN: No shopping link for ingredient uid '{ingr.uid}'")

        return ShoppingListItem(text=ingr.text, link=link.link if link else "")

    return ShoppingList(items=[to_item(ingr) for ingr in recipe.ingredients])
