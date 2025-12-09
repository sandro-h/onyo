from pathlib import Path
import re
import http.server

from onyo_backend.shopping_list import assemble_shopping_list, get_shopping_links
from .recipes import NUM_COLORS, Mise
from onyo_backend.recipes import list_recipes
from jinja2 import Environment, PackageLoader, select_autoescape

PORT = 13012


def main():
    with http.server.ThreadingHTTPServer(("", PORT), SimpleRequestHandler) as httpd:
        print(f"Listening on port http://localhost:{PORT}")
        httpd.serve_forever()


class SimpleRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.template_env = Environment(
            loader=PackageLoader("onyo_backend"), autoescape=select_autoescape()
        )

        self.routes = {
            r"/onyo": self.render_categories,
            r"/onyo/categories/([^/]+)": self.render_recipe_list,
            r"/onyo/recipes/([^/]+)": self.render_recipe,
        }

        super().__init__(*args, directory=Path(__file__).parent, **kwargs)

    def do_GET(self):
        if self.path.startswith("/onyo/static"):
            return super().do_GET()

        if self.path == "/onyo/favicon.ico":
            return self._reply(404, "Not found")

        for pattern, route in self.routes.items():
            m = re.fullmatch(pattern, self.path)
            if m:
                if m.groups():
                    return route(*m.groups())

                return route()

        return self._reply(404, "Not found")

    def render_categories(self):
        categories, _ = list_recipes()
        self.reply_template("index.html", categories=categories)

    def render_recipe_list(self, category_name):
        categories, _ = list_recipes()
        category = categories.get(category_name.lower())
        if not category:
            self._reply(404, f"No category {category_name}")
            return

        self.reply_template("recipe_list.html", category=category)

    def render_recipe(self, recipe_id):
        _, recipes = list_recipes()
        shopping_links = get_shopping_links()

        recipe = recipes.get(recipe_id.lower())
        if not recipe:
            self._reply(404, f"No recipe {recipe_id}")
            return

        shopping_list = assemble_shopping_list(recipe, shopping_links)
        back_link = f"/onyo/categories/{list(recipe.categories)[0]}"

        self.reply_template(
            "recipe.html",
            recipe=recipe,
            shopping_list=shopping_list,
            Mise=Mise,
            NUM_COLORS=NUM_COLORS,
            back_link=back_link,
        )

    def reply_template(self, template_file, **kw_args):
        template = self.template_env.get_template(template_file)
        self._reply(200, template.render(kw_args), "text/html")

    def _reply(self, status, body, content_type=None):
        self.send_response(status)
        if content_type:
            self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(body.encode())


if __name__ == "__main__":
    main()
