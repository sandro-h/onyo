from pathlib import Path
import re
import shutil
from onyo_backend.__main__ import recipe_link
from onyo_backend.ideas import list_ideas_for_html
from onyo_backend.recipes import (
    NUM_COLORS,
    RECIPE_DIR,
    Mise,
    load_recipes,
    load_recipes_uncached,
    print_errors,
    print_warnings,
)
import typer
import rich
from onyo_backend import shopping_list
from jinja2 import Environment, PackageLoader, select_autoescape

STATIC_DIR = Path(__file__).parent.parent / "onyo_backend" / "onyo" / "static"
app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def update_shopping_links(
    origins: bool = typer.Option(
        default=False, help="Show origin(s) of each ingredient"
    )
):
    shopping_list.update_shopping_links(origins)


@app.command()
def validate():
    errors = []
    _, recipes = load_recipes_uncached(RECIPE_DIR, errors)

    has_warnings = any((r.warnings for r in recipes.values()))
    if not errors and not has_warnings:
        rich.print("[green]✅ All good[/green]")
    else:
        print_errors(errors)
        print_warnings(recipes.values())
        rich.print("[red]❌ There are problems[/red]")


@app.command()
def generate_static(output_dir: Path, recipe_dir: Path = typer.Option(RECIPE_DIR)):
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(STATIC_DIR, output_dir / "static", dirs_exist_ok=True)

    template_env = Environment(
        loader=PackageLoader("onyo_backend"), autoescape=select_autoescape()
    )

    categories, recipes = load_recipes(recipe_dir, 0)
    ideas = list_ideas_for_html()
    shopping_ingredients = shopping_list.get_shopping_ingredients()

    index_page = render(
        template_env,
        "index.html",
        categories=categories,
        user=None,
        recipes=recipes.values(),
    )
    index_page = re.sub(
        r'href="/onyo/categories/([^"]+)"', r'href="cat_\1.html"', index_page
    )
    index_page = re.sub(
        r'href="/onyo/recipes/([^"]+)"', r'href="rec_\1.html"', index_page
    )
    index_page = index_page.replace('href="/onyo/ideas"', 'href="ideas.html"')
    write_page(output_dir / "index.html", index_page)

    generate_page(
        template_env,
        "ideas.html",
        output_dir / "ideas.html",
        ideas=ideas,
        user=None,
    )

    for category in categories.values():
        generate_category_page(
            template_env, output_dir / f"cat_{category.name}.html", category
        )

    for recipe in recipes.values():
        generate_recipe_page(
            template_env,
            output_dir / f"rec_{recipe.id}.html",
            recipe,
            shopping_ingredients,
        )


def generate_category_page(template_env, output_file, category):
    cat_page = render(
        template_env,
        "recipe_list.html",
        category=category,
    )

    cat_page = re.sub(r'href="/onyo/recipes/([^"]+)"', r'href="rec_\1.html"', cat_page)
    cat_page = cat_page.replace('href="/onyo"', 'href="index.html"')
    write_page(output_file, cat_page)


def generate_recipe_page(template_env, output_file, recipe, shopping_ingredients):
    shop_list = shopping_list.assemble_shopping_list(recipe, shopping_ingredients)
    link = recipe_link(recipe.id)
    back_link = f"cat_{list(recipe.categories)[0]}.html"

    generate_page(
        template_env,
        "recipe.html",
        output_file,
        recipe=recipe,
        shopping_list=shop_list,
        Mise=Mise,
        NUM_COLORS=NUM_COLORS,
        link=link,
        back_link=back_link,
        user=None,
    )


def generate_page(template_env, template_file, output_file, **kw_args):
    content = render(template_env, template_file, **kw_args)
    write_page(output_file, content)


def render(template_env, template_file, **kw_args):
    template = template_env.get_template(template_file)
    return template.render(kw_args).replace("/onyo/static", "static")


def write_page(output_file, content):
    with open(output_file, "w", encoding="utf8") as file:
        file.write(content)


if __name__ == "__main__":
    app()
