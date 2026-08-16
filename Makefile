# Makefile for local quality, tests and the offline demo.

PYTHON ?= poetry run python
PYTEST ?= poetry run pytest
SRC := src tests

.PHONY: install lint format typecheck test test-integration audit compose-up demo check-migrations

install:
	poetry install --no-root
	poetry run pre-commit install

lint:
	poetry run ruff check $(SRC)
	poetry run ruff format --check $(SRC)

format:
	poetry run ruff check --fix $(SRC)
	poetry run ruff format $(SRC)

typecheck:
	poetry run mypy src/core src/providers src/apps/playlist_sync/diffing.py src/apps/playlist_sync/matching.py src/apps/playlist_sync/state.py src/apps/playlist_sync/jobs.py

test:
	$(PYTEST) tests/unit tests/failure

test-integration:
	$(PYTEST) tests/integration

audit:
	poetry run pip-audit

check-migrations:
	SYNC_TESTING=1 PYTHONPATH=src $(PYTHON) src/manage.py makemigrations --check --dry-run

compose-up:
	docker compose up --build

demo:
	SYNC_TESTING=1 SYNC_PROVIDER_MODE=fake PYTHONPATH=src $(PYTHON) scripts/demo.py
