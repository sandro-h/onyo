from onyo_backend.recipes import (
    RECIPE_DIR,
    load_recipes_uncached,
    print_errors,
    print_warnings,
)
import typer
import rich
from onyo_backend import shopping_list


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


if __name__ == "__main__":
    app()
