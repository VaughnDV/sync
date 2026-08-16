# Security policy

## Reporting

Email the maintainer via the GitHub profile on this repository. Do not open public issues for token leaks, injection, or authentication bypasses.

## Scope

This application stores encrypted Spotify tokens, user passwords (Django), and job metadata. Provider API keys live in environment variables, never in the repository.

## What we already do

- Fernet encryption for Spotify access and refresh tokens
- Tokens excluded from Django admin, logs, exceptions and `__repr__`
- CSRF on mutating views; HttpOnly session/CSRF cookies; Secure cookies when `DEBUG` is false
- Per-user ownership checks on job, status, review, cancel and playlist endpoints
- Minimum Spotify OAuth scopes
- CI secret scanning (gitleaks) and dependency audit (`pip-audit`)

## Out of scope for the showcase

Live provider accounts, third-party outages, and quota exhaustion of YouTube/Spotify/OpenAI.
