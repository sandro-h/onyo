# Onyo

Start:

Make sure you have a `backend/.passphrase` file for the `key.pem`.

```shell
make start
```

or

```shell
.\start.ps1
```

http://localhost:13012/

The app should be put behind nginx for SSL termination.

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

Start backend:

```shell
cd backend
.\venv\Scripts\Activate.ps1
python -m onyo_backend
```

With hot reloading (buggy):

```shell
python -m jurigged -m onyo_backend
```

Tests and linting:

```shell
make lint
make test
```
