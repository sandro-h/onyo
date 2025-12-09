import typer
from onyo_backend import shopping_list


app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def update_shopping_links(
    origins: bool = typer.Option(
        default=False, help="Show origin(s) of each ingredient"
    )
):
    shopping_list.update_shopping_links(origins)


@app.command(hidden=True)
def remove_me_when_more_than_one_command():
    pass


if __name__ == "__main__":
    app()
