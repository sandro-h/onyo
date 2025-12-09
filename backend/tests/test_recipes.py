from pathlib import Path
import pytest

from onyo_backend.recipes import (
    create_empty_recipe,
    load_recipe,
    load_recipe_from_file,
    normalize_for_recipe_id,
    resolve_links,
)


@pytest.mark.golden_test("test_data/test_recipe.valid.*.golden.yaml")
def test_load_recipe_valid(golden):
    recipe = load_recipe(golden["input"], "testrecipe")
    assert recipe.to_dict() == golden.out["output"]


@pytest.mark.golden_test("test_data/test_recipe.warnings.*.golden.yaml")
def test_load_recipe_warnings(golden):
    recipe = load_recipe(golden["input"], "testrecipe")
    resolve_links({recipe.id: recipe})
    assert {"warnings": [w.to_dict() for w in recipe.warnings]} == golden.out["output"]


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


def test_create_empty_recipe(tmp_path):
    recipe_dir: Path = tmp_path / "recipes"
    recipe_dir.mkdir()

    recipe_id = create_empty_recipe("Dummy Recipe", recipe_dir=recipe_dir)
    recipe = load_recipe_from_file(recipe_dir / f"{recipe_id}.yaml")

    assert recipe.id == "dummyrecipe"
    assert recipe.name == "Dummy Recipe"
    assert recipe.categories == {"Meal"}
