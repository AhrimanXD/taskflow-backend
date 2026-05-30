# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Realtime Collaborative Task Manager — FastAPI backend with PostgreSQL, SQLAlchemy 2.0, Alembic, and JWT auth. Python 3.13+ is required. Dependencies are managed with **uv**.

## Commands

```bash
# Install dependencies
uv sync

# Run dev server (auto-reload)
uv run fastapi dev main.py

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
uv run alembic downgrade -1
```

Copy `.env.example` to `.env` and fill in `DATABASE_URL` and `SECRET_KEY` before starting.

## Architecture

The app is split into five layers that map to five directories under `app/`:

| Layer | Directory | Responsibility |
|---|---|---|
| Models | `app/models/` | SQLAlchemy ORM table definitions |
| Schemas | `app/schemas/` | Pydantic request/response shapes |
| CRUD | `app/crud/` | Raw DB queries — no HTTP concerns |
| Services | `app/services/` | Cross-cutting logic (auth guards, business rules) |
| Routes | `app/api/routes/` | FastAPI path functions — thin, delegate to CRUD/services |

`main.py` creates the app, registers CORS, and mounts all routers. Each router registers itself in `app/api/routes/__init__.py` and is mounted in `main.py` with a prefix (`/api/auth`, `/api/tasks`, `/api/workspaces`).

### Auth flow

`app/api/dependencies.py` exposes two Annotated type aliases used across all protected routes:

- `SessionDep` — injects a SQLAlchemy session
- `CurrentUser` — validates the Bearer token, fetches and returns the `User` ORM object, raises 401 on failure

JWT tokens are signed with HS256. The `sub` claim holds the `user_id` as a string. Passwords are hashed with Argon2 via Passlib.

### Workspace membership

`WorkspaceMember` is a join table between `User` and `Workspace` with a `role` column (`owner`, `admin`, `member`). When a workspace is created, the creator is automatically added as a `WorkspaceMember` with `role="owner"`.

`app/services/workspace.py` provides `get_workspace_or_raise(db, workspace_id, user_id, require_owner=False)` — a shared guard used by all workspace routes that centralises 404 and 403 checks:

- `require_owner=False` (default): passes if the user is the owner or any member
- `require_owner=True`: passes only if the user is the owner

Use this pattern — not inline HTTPException blocks — for any new workspace routes.

### Adding a new domain

1. Create `app/models/<domain>.py` (SQLAlchemy mapped class, import in `app/models/__init__.py`)
2. Create `app/schemas/<domain>.py` (Base, Create, Update, Response Pydantic models)
3. Create `app/crud/<domain>.py` (query functions, import in `app/crud/__init__.py`)
4. Create `app/api/routes/<domain>.py` (router, add to `app/api/routes/__init__.py` and mount in `main.py`)
5. Generate and run an Alembic migration
