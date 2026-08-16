# Contributing

## Setup

```bash
make install
cp .env.example .env
make test
```

Use fixture mode (`SYNC_PROVIDER_MODE=fake`) unless you are changing a live adapter.

## Checks before a PR

```bash
make lint
make typecheck
make test
make test-integration
make check-migrations
```

Pre-commit hooks run Ruff, mypy on typed modules, JSON/TOML/YAML validation, merge-conflict detection, EOF/whitespace fixes, and private-key detection.

## Style

- Keep provider SDKs behind `providers/` adapters.
- Persist user-facing `error_code` values, never raw SDK exceptions.
- New behaviour needs a unit or failure test.

## Architecture

Product decisions live in [docs/adr](docs/adr). Open a new ADR if you change input types, sync mode, budgets or the security baseline.
