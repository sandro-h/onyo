import pytest

from onyo_backend.recipes import load_recipe


@pytest.mark.golden_test("test_data/*.golden.yaml")
def test_load_recipe(golden):
    recipe = load_recipe(golden["input"], "testrecipe")
    assert recipe.to_dict() == golden.out["output"]
