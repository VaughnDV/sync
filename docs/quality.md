# Local quality commands

Use the Makefile for developer checks:

```bash
make install            # poetry install and pre-commit hooks
make lint               # ruff lint + format check
make typecheck          # mypy on new typed modules
make test               # unit and failure tests
make test-integration   # Django/Celery/offline flow
make check-migrations   # python src/manage.py makemigrations --check --dry-run
make audit              # pip-audit
make compose-up         # docker compose
make demo               # one-command offline fixture demo
```

Pre-commit runs Ruff, mypy on typed modules, TOML/YAML/JSON validation, merge-conflict detection, EOF/whitespace fixes, and private-key detection.
