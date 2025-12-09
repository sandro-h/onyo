import pytest

from onyo_backend.shopping_list import ShoppingLinks, assemble_shopping_list
from onyo_backend.recipes import load_recipe


@pytest.mark.golden_test("test_data/test_shopping_list*.golden.yaml")
def test_assemble_shopping_list(golden):
    # Given
    recipe = load_recipe(golden["input"]["recipe"], "testrecipe")
    shopping_links = ShoppingLinks.from_dict(golden["input"]["shopping_links"])

    # When
    shopping_list = assemble_shopping_list(recipe, shopping_links)

    # Then
    assert shopping_list.to_dict() == golden.out["output"]
