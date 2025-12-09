.PHONY: lint
lint:
	pylint backend/onyo_backend

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
