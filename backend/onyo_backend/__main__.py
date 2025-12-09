from dataclasses import dataclass
from pathlib import Path
import re
import http.server
from urllib.parse import unquote_plus

import yaml

from .ideas import Idea, add_idea, delete_idea, list_ideas_for_html
from .shopping_list import assemble_shopping_list, get_shopping_ingredients
from .recipes import NUM_COLORS, Mise, load_recipe, load_recipe_yaml, save_recipe_yaml
from onyo_backend.recipes import list_recipes
from jinja2 import Environment, PackageLoader, select_autoescape

PORT = 13012
RECIPE_EDITOR = "recipe_editor"
IDEA_EDITOR = "idea_editor"
USER_ROLE_MAPPING = {
    "admin": {IDEA_EDITOR, RECIPE_EDITOR},
    "fam": {IDEA_EDITOR},
}


@dataclass
class AuthenticatedUser:
    name: str
    roles: set[str]


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
            r"/onyo/recipes/([^/]+)/?": self.render_recipe,
            r"/onyo/recipes/([^/]+)/edit": self.render_edit_recipe,
            r"/onyo/ideas": self.render_ideas,
        }

        self.post_routes = {
            r"/onyo/ideas": self.add_idea,
            r"/onyo/ideas/([^/]+)": self.delete_idea,
            r"/onyo/recipes/([^/]+)/edit": self.edit_recipe,
        }

        super().__init__(*args, directory=Path(__file__).parent, **kwargs)

    def do_GET(self):
        if self.path.startswith("/onyo/static"):
            super().do_GET()
        elif self.path == "/onyo/favicon.ico":
            self._reply(404, "Not found")
        else:
            self.execute_route(self.routes)

    def do_POST(self):
        self.execute_route(self.post_routes)

    def execute_route(self, routes):
        for pattern, route in routes.items():
            m = re.fullmatch(pattern, self.path)
            if m:
                route(*m.groups())
                return

        self._reply(404, "Not found")

    def render_categories(self):
        categories, recipes = list_recipes()
        self.reply_template(
            "index.html",
            categories=categories,
            recipes=recipes.values(),
            user=self.get_authenticated_user(),
        )

    def render_recipe_list(self, category_name):
        categories, _ = list_recipes()
        category = categories.get(category_name.lower())
        if not category:
            self._reply(404, f"No category {category_name}")
            return

        self.reply_template("recipe_list.html", category=category)

    def render_recipe(self, recipe_id):
        recipe = self.lookup_recipe(recipe_id)
        if not recipe:
            return

        shopping_ingredients = get_shopping_ingredients()
        shopping_list = assemble_shopping_list(recipe, shopping_ingredients)
        link = recipe_link(recipe_id)
        back_link = f"/onyo/categories/{list(recipe.categories)[0]}"

        self.reply_template(
            "recipe.html",
            recipe=recipe,
            shopping_list=shopping_list,
            Mise=Mise,
            NUM_COLORS=NUM_COLORS,
            link=link,
            back_link=back_link,
            user=self.get_authenticated_user(),
        )

    def render_edit_recipe(self, recipe_id):
        recipe = self.lookup_recipe(recipe_id)
        if not recipe:
            return

        recipe_yaml = load_recipe_yaml(recipe.id)

        self.reply_template(
            "edit_recipe.html",
            recipe=recipe,
            recipe_yaml=recipe_yaml,
        )

    def edit_recipe(self, recipe_id):
        if not self.check_role(RECIPE_EDITOR):
            return

        if not self.lookup_recipe(recipe_id):
            return

        body_data = self.get_body_text()
        # poor man's form parsing, since it's only one value
        recipe_yaml = unquote_plus(body_data[len("recipe_yaml=") :]).replace("\r", "")

        # Try to load the recipe to make sure it's valid
        try:
            data = yaml.safe_load(recipe_yaml)
            load_recipe(data, recipe_id.lower())
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._reply(400, f"Invalid recipe: {e}")
            return

        save_recipe_yaml(recipe_id, recipe_yaml)

        # redirect to avoid repost on refresh
        self.redirect(recipe_link(recipe_id))

    def lookup_recipe(self, recipe_id):
        _, recipes = list_recipes()

        recipe = recipes.get(recipe_id.lower())
        if not recipe:
            self._reply(404, f"No recipe {recipe_id}")
            return None

        return recipe

    def render_ideas(self):
        ideas = list_ideas_for_html()
        self.reply_template(
            "ideas.html",
            ideas=ideas,
            user=self.get_authenticated_user(),
        )

    def add_idea(self):
        if not self.check_role(IDEA_EDITOR):
            return

        body_data = self.get_body_text()
        # poor man's form parsing, since it's only one value
        text = unquote_plus(body_data[len("text=") :])

        add_idea(Idea(text))

        # redirect to avoid repost on refresh
        self.redirect("/onyo/ideas")

    def delete_idea(self, idea_guid):
        if not self.check_role(IDEA_EDITOR):
            return

        body_data = self.get_body_text()
        if body_data != "action=delete":
            self._reply(400, "Invalid action")
            return

        delete_idea(idea_guid)

        # redirect to avoid repost on refresh
        self.redirect("/onyo/ideas")

    def get_body_text(self):
        content_length = int(self.headers["Content-Length"])
        return bytes.decode(self.rfile.read(content_length))

    def check_role(self, required_role):
        user = self.get_authenticated_user()

        if not user:
            self._reply(401, "Not authenticated")
            return False
        if required_role not in user.roles:
            self._reply(403, "You do not have permission for this operation")
            return False

        return True

    def get_authenticated_user(self) -> AuthenticatedUser:
        # Relies on nginx config to forward user in this header:
        username = self.headers.get("X-User")
        if not username:
            return None
        return AuthenticatedUser(
            name=username,
            roles=USER_ROLE_MAPPING.get(username, set()),
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

    def redirect(self, path):
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()


def recipe_link(recipe_id):
    return f"/onyo/recipes/{recipe_id}"


if __name__ == "__main__":
    main()
