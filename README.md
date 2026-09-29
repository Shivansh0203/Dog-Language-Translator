# PawAI Complete Project

This archive contains the PawAI frontend plus the FastAPI/PostgreSQL authentication backend.

## What is included

- `frontend/` — authentication-wired PawAI web UI.
- `frontend-original/` — untouched original frontend for reference.
- `backend/` — FastAPI + SQLAlchemy + PostgreSQL + Alembic backend.
- `docker-compose.yml` — optional local stack that runs PostgreSQL, FastAPI, and nginx without installing Python/PostgreSQL directly.

## Important: why the browser previously said "Could not reach the PawAI server"

The frontend was configured to call `http://localhost:8000`, but no FastAPI server was running there. A static HTML file cannot start a database-backed API by itself.

The frontend API helper now supports same-origin deployment. When the frontend is served by the included nginx Docker setup, browser requests go to `/api/...` and nginx proxies them to FastAPI.

## Easiest local run (Docker)

Install Docker Desktop, then from this folder run:

```bash
docker compose up --build
```

Open:

```text
http://localhost:8080/01-create-account.html
```

The first startup creates the PostgreSQL container and runs the Alembic migration automatically.

To stop:

```bash
docker compose down
```

To stop and remove the local database volume too:

```bash
docker compose down -v
```

The database password in `docker-compose.yml` is for local development only. Change it before using any shared environment.

## Without Docker

See `backend/README.md` for the Python/PostgreSQL setup. The backend has not been executed in the original Claude sandbox, so end-to-end runtime verification must happen in a real environment.

## Frontend API configuration

`frontend/assets/js/api.js` supports `window.PAWAI_API_BASE_URL` for a separately hosted API. If no override is provided and the page is served over HTTP/HTTPS, it uses the current origin, which works with the included nginx reverse proxy. For a development frontend on another port, define `window.PAWAI_API_BASE_URL = "http://localhost:8000"` before loading `api.js`.

## Security status

The current implementation uses Argon2id password hashing, opaque server-side sessions, HttpOnly cookies, SameSite=Lax, authentication/authorization checks, ownership checks for pets, an in-process auth rate limiter, and no authentication tokens in localStorage/sessionStorage.

Known deferred features: password reset/email verification, pet-avatar upload, and persisted settings. The chatbot remains the existing rule-based placeholder.

For multi-instance production deployment, replace the in-process auth rate limiter with a shared store such as Redis and run the backend/database behind HTTPS with secure cookies.
