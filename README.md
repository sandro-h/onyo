# Onyo

http://localhost:13012/

The app should be put behind nginx for SSL termination. Additionally, nginx can be configured for basic auth so
that editing operations are protected. Example nginx config:

```
location /onyo {
    proxy_pass http://127.0.0.1:13012/onyo;
    auth_basic "Onyo";
    auth_basic_user_file .onyo_htpasswd;
}
```

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