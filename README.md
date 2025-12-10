# Onyo

http://localhost:13012/onyo

The app should be put behind nginx for SSL termination. Additionally, nginx can be configured for basic auth so
that editing operations are protected. Example nginx config:

```
location /onyo {
    proxy_pass http://127.0.0.1:13012/onyo;
    auth_basic "Onyo";
    auth_basic_user_file .onyo_htpasswd;
    proxy_set_header X-User $remote_user;
}
```

## Writing recipes

Recipes are stored in the `data/recipes` folder as yaml files.

**Recommendation**: put a dedicated `onyo-data` git repo into `data/` to maintain these recipes. Then use `push_data.ps1` to commit and push changes.

### Special syntaxes

#### In ingredient list
* `$ingredient$` - used in ingredient list and task descriptions to establish a link
* `$ingredient:num$` - used to disambiguate the same ingredient used in different proportions / steps. For example: `$salt:1$` and `$salt:2$`
* `~recipe_id~` - ingredient is a link to another recipe. `recipe_id` is the name of the recipe file without `.yaml`.
* `=Title=` - add a title for the following ingredients
* ` - (`  and `- )` - group ingredients together (prepared/cooked together). Example:
  ```
  - (
  - $onions$
  - $garlic$
  - )
  ```

#### In tasks
* `!10 minutes!` - timer link in task description
* `**bold text**`

### CLI

#### Validate recipes

```shell
.\cli.ps1 validate
```

#### Update shopping links

```shell
.\cli.ps1 update-shopping-links
```

Will warn about missing links and mention new ingredients (only on first execution).

**Pay attention to duplicate ingredients with slightly different names and try to align them in the recipes.**

To see where the ingredients comes from:

```shell
.\cli.ps1 update-shopping-links --origins
```

#### Generate static page

```shell
.\cli.ps1 generate-static generated/
```

Generates a static version of all the Onyo pages based on the `data` folder. These pages don't support edit operations obviously.

## Development

Uses a simple Python backend with Jinja for html templating.
This serves a very simple webpage that also functions as a Progressive Web App so it can be "installed" on the phone.

All the data (recipes) come from the `data` folder. Recipe changes are hot loaded, so no need to restart the backend.

The webpage contains `launchtimer://` links to start a timer on the phone. This only works if
the companion TimerLauncher app is installed. It handles URLs with this scheme and creates
an appropriate SET_ALARM intent (which the webpage cannot do directly). It would nice
if the built-in alarm app supported such links directly, but alas.

Setup backend:

```shell
cd backend
python3 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start/stop/restart backend:

```shell
make start
make stop
make restart
```

Start backend manually:

```shell
cd backend
.\venv\Scripts\Activate.ps1
python -m onyo_backend
```

With hot reloading (may be buggy):

```shell
make dev
```

Tests and linting:

```shell
make lint
make test
```

Upgrade all dependencies:

```shell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.in
pip freeze > requirements.txt
```
