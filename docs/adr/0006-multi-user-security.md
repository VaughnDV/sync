# ADR 0006: Multi-user application and security baseline

## Status

Accepted

## Context

The app already has registration, login, and per-user jobs, but tokens are stored in plaintext, admin shows tokens, allowed hosts are hard-coded to a personal domain, and some endpoints can leak provider errors.

## Decision

This is a **multi-user application**. Security and operations match that claim:

- Every job, status, review, apply, and cancel endpoint is authenticated and scoped to `request.user`.
- Spotify access and refresh tokens are encrypted at rest with Fernet. They are never displayed in admin, logs, exceptions, or `__repr__`.
- Templates use a `spotify_connected` flag, not the token value.
- Spotify OAuth requests the minimum scopes: `playlist-read-private` and `playlist-modify-private`.
- Disconnect clears and optionally revokes tokens. Expired tokens are refreshed; revoked tokens force reconnect with `SPOTIFY_REVOKED`.
- Allowed hosts, trusted origins, cookie security, log level, and provider mode come from validated environment configuration.
- CSRF remains enabled. Session and CSRF cookies are `Secure` + `HttpOnly` in production; `Secure` is off only when `DEBUG` is true on localhost.
- Provider exceptions are mapped to stable error codes. Raw SDK text is not shown to users.

Single-user demo mode is a deployment choice (`SYNC_PROVIDER_MODE=fake`), not a different security model.

## Consequences

- Users must reconnect Spotify after deploying encryption if old plaintext tokens exist.
- Django admin shows connection status, never credential material.
- Tests cover CSRF, session cookies, and cross-user access denials.
