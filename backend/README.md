# PawAI Backend

FastAPI + PostgreSQL + SQLAlchemy + Alembic authentication service for PawAI.
Argon2id password hashing and server-side sessions in an HttpOnly cookie.

## Prerequisites

Either:

- Python 3.11+ and PostgreSQL 14+, or
- Docker (the repository root contains `docker-compose.yml`).

## Local Python setup

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## API

- `POST /api/auth/register` — creates a user and optional pet and auto-logs in.
- `POST /api/auth/login` — login by username or email.
- `POST /api/auth/logout` — invalidates the current server-side session.
- `GET /api/auth/me` — current authenticated user.
- `GET/POST /api/pets` — pets belonging to the authenticated user.

## Security notes

- Passwords are hashed with Argon2id and never returned by API responses.
- Sessions contain only an opaque UUID in the browser cookie; session state is stored server-side.
- Auth endpoints have a dependency-free in-process rate limiter. For a multi-worker/multi-instance deployment, replace it with a shared Redis-backed limiter.
- Pet ownership is checked server-side and unauthorized pet IDs return 404 to avoid confirming another user's resource exists.
- `SESSION_COOKIE_SECURE=true` is required when serving over HTTPS.
- `CORS_ORIGINS` must contain exact allowed frontend origins when frontend and API are on different origins. Never use `*` with credentialed requests.

## Tests

The test suite is written for PostgreSQL. Run it in an environment with the required dependencies and a disposable test database:

```bash
pytest -v
```

The original Claude sandbox could not execute PostgreSQL or install dependencies, so test results are not claimed here.

## Deferred features

Password reset/email verification are intentionally not implemented in this milestone. Pet-avatar upload and persistent settings require additional backend endpoints.
