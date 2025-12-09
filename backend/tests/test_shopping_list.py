import pytest

from onyo_backend.shopping_list import assemble_shopping_list, load_shopping_ingredients
from onyo_backend.recipes import load_recipe


@pytest.mark.golden_test("test_data/test_shopping_list*.golden.yaml")
def test_assemble_shopping_list(golden, tmp_path):
    # Given
    recipe = load_recipe(golden["input"]["recipe"], "testrecipe")

    shopping_links_path = tmp_path / "shopping_links.yaml"
    with open(shopping_links_path, "w", encoding="utf8") as file:
        for k, v in golden["input"]["shopping_links"].items():
            file.write(f"{k}: {v}\n")

    shopping_ingredients = load_shopping_ingredients(shopping_links_path)

    # When
    shopping_list = assemble_shopping_list(recipe, shopping_ingredients)

    # Then
    assert shopping_list.to_dict() == golden.out["output"]
