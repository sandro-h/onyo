import pytest

from onyo_backend.recipes import load_recipe, normalize_for_recipe_id


@pytest.mark.golden_test("test_data/test_recipe*.golden.yaml")
def test_load_recipe(golden):
    recipe = load_recipe(golden["input"], "testrecipe")
    assert recipe.to_dict() == golden.out["output"]


@pytest.mark.parametrize(
    "name, expected",
    [
        ("bananas", "bananas"),
        ("Apple Pie", "applePie"),
        ("French Onion Soup", "frenchOnionSoup"),
        ("Shepherd's Pie", "shepherdsPie"),
        ("abc_def-geh 123", "abcDefGeh123"),
    ],
)
def test_normalize_for_recipe_id(name, expected):
    assert normalize_for_recipe_id(name) == expected
