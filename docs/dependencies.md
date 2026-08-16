# Dependency policy

- Python 3.11–3.13 and Django 5.2 LTS are the supported runtime.
- `poetry.lock` is committed so installs are reproducible.
- Direct dependencies are ranged; transitive HTTP libraries are not pinned unless a CVE forces it.
- Authentication uses `social-auth-app-django` only. The obsolete `python-social-auth` package is not used.
- `pip-audit` runs locally (`make audit`) and in CI.
- Dependency updates are reviewed intentionally: update the relevant Poetry constraint or pinned Action/image, regenerate the lock file, and run the complete CI suite before merging.
