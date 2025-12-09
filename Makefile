.PHONY: lint
lint:
	pylint backend/onyo_backend

.PHONY: test
test:
	pytest -vv backend/tests

.PHONY: start
start:
	powershell -ExecutionPolicy Bypass -File .\start.ps1
