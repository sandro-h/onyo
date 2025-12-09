from datetime import datetime
import os
from pathlib import Path
import re
import http.server
import time
from onyo_backend.recipes import list_recipes
from jinja2 import Environment, PackageLoader, select_autoescape
import ssl

PORT = 13012


def main():
    with http.server.ThreadingHTTPServer(("", PORT), SimpleRequestHandler) as httpd:
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.check_hostname = False
        ssl_ctx.load_cert_chain(
            certfile="certificate.pem",
            keyfile="key.pem",
            password=os.getenv("PASSPHRASE"),
        )
        httpd.socket = ssl_ctx.wrap_socket(httpd.socket, server_side=True)

        print(f"Listening on port http://localhost:{PORT}")
        httpd.serve_forever()


class SimpleRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.template_env = Environment(
            loader=PackageLoader("onyo_backend"), autoescape=select_autoescape()
        )

        self.routes = {
            r"/": self.render_categories,
            r"/([^/]+)": self.render_recipe_list,
            r"/([^/]+)/([^/]+)": self.render_recipe,
        }

        super().__init__(*args, directory=Path(__file__).parent, **kwargs)

    def do_GET(self):
        if self.path.startswith("/static"):
            return super().do_GET()

        if self.path == "/favicon.ico":
            return self._reply(404, "Not found")

        for pattern, route in self.routes.items():
            m = re.fullmatch(pattern, self.path)
            if m:
                if m.groups():
                    return route(*m.groups())

                return route()

        self._reply(404, "Not found")

    def render_categories(self):
        categories = list_recipes()
        return self.reply_template("index.html", categories=categories)

    def render_recipe_list(self, category_name):
        categories = list_recipes()
        category = categories[category_name.lower()]
        return self.reply_template("recipe_list.html", category=category)

    def render_recipe(self, category_name, recipe_id):
        categories = list_recipes()
        category = categories[category_name.lower()]
        recipe = next((r for r in category.recipes if r.id == recipe_id.lower()), None)
        return self.reply_template("recipe.html", recipe=recipe)

    def reply_template(self, template_file, **kw_args):
        template = self.template_env.get_template(template_file)
        self._reply(200, template.render(kw_args), "text/html")

    # def reply_static_file(self, file_name):
    #     path = Path("static") / file_name
    #     if not path.exists():
    #         self._reply(404, "Not found")
    #         return

    #     with open(path, "rb") as file:
    #         self.send_response(200)
    #         self.send_header("Content-type", content_type)
    #         self.end_headers()
    #         self.wfile.write(file.read())

    # def guess_content_type(self, file):
    #     mappings =
    #     ext = file.split(".")[-1]
    #     if file.endswith(".json"):
    #         return "application/json"

    def _reply(self, status, body, content_type=None):
        self.send_response(status)
        if content_type:
            self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(body.encode())


if __name__ == "__main__":
    main()
