check: lint test

.PHONY: lint
lint:
	flake8 backend/onyo_backend backend/cli backend/tests

.PHONY: test
test:
	pytest -vv backend/tests

.PHONY: start
start:
	powershell -ExecutionPolicy Bypass -File .\start.ps1

.PHONY: stop
stop:
	powershell -ExecutionPolicy Bypass -File .\stop.ps1

restart: stop start

.PHONY: dev
dev:
	powershell -ExecutionPolicy Bypass -File .\dev.ps1
