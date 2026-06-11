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

| Layer    | Directory         | Responsibility                                           |
| -------- | ----------------- | -------------------------------------------------------- |
| Models   | `app/models/`     | SQLAlchemy ORM table definitions                         |
| Schemas  | `app/schemas/`    | Pydantic request/response shapes                         |
| CRUD     | `app/crud/`       | Raw DB queries — no HTTP concerns                        |
| Services | `app/services/`   | Cross-cutting logic (auth guards, business rules)        |
| Routes   | `app/api/routes/` | FastAPI path functions — thin, delegate to CRUD/services |

`main.py` creates the app, registers CORS, and mounts all routers. Each router registers itself in `app/api/routes/__init__.py` and is mounted in `main.py` with a prefix (`/api/auth`, `/api/tasks`, `/api/workspaces`; the invitation and workspace-task routers carry their own full paths and mount at `/api`).

### Auth flow

`app/api/dependencies.py` exposes two Annotated type aliases used across all protected routes:

- `SessionDep` — injects a SQLAlchemy session
- `CurrentUser` — validates the Bearer token, fetches and returns the `User` ORM object, raises 401 on failure

JWT tokens are signed with HS256. The `sub` claim holds the `user_id` as a string. Passwords are hashed with Argon2 via Passlib.

### Workspace membership

`WorkspaceMember` is a join table between `User` and `Workspace` with a `role` column (`owner`, `admin`, `member`). When a workspace is created, the creator is automatically added as a `WorkspaceMember` with `role="owner"`.

`app/services/workspace.py` provides three shared guards that centralise 404/403 checks. Use these — not inline HTTPException blocks — for any new workspace-scoped routes:

- `get_workspace_or_raise(db, workspace_id, user_id, require_owner=False)` — returns the `Workspace`; 404 if missing, 403 unless the user is the owner or a member (`require_owner=True` restricts to the owner — used by workspace update/delete)
- `get_member_role_or_raise(db, workspace_id, user_id)` — returns the caller's `RoleEnum`; 404 if the workspace is missing, 403 if not a member. Use when the route needs the role for further checks
- `require_role_or_raise(db, workspace_id, user_id, allowed={...})` — like the above but 403s unless the role is in `allowed` (e.g. `{RoleEnum.OWNER, RoleEnum.ADMIN}`) — used by the invitation routes

### Tasks — two route trees

Tasks are workspace-optional (`workspace_id` nullable). There are deliberately **two separate route trees**, each with one uniform auth model — never one endpoint set that branches on "has a workspace or not":

| Tree | Routes | Scope |
|---|---|---|
| Personal | `/api/tasks/*` | Owner-only, fenced to `workspace_id IS NULL`. Not assignable (`assignee_id` ignored) |
| Workspace | `/api/workspaces/{workspace_id}/tasks/*` | Membership-scoped, full CRUD |

Workspace-tree permission matrix (guards live in `app/services/task.py`):

| Action | Who |
|---|---|
| List / create / get / edit (incl. assign) | Any member |
| Assign / reassign | Any member; assignee must be an **active member** of that workspace else 400; rank-blind; explicit `null` = unassign |
| Delete | Task creator (`owner_id`) OR workspace owner/admin |

`get_workspace_task_or_raise` loads the task, verifies `task.workspace_id == workspace_id` (404 on mismatch — the IDOR check below), then checks membership; it returns `(task, role)`. `workspace_id` always comes from the path, never the request body (`TaskCreate` doesn't have it).

### Adding a new domain

1. Create `app/models/<domain>.py` (SQLAlchemy mapped class, import in `app/models/__init__.py`)
2. Create `app/schemas/<domain>.py` (Base, Create, Update, Response Pydantic models)
3. Create `app/crud/<domain>.py` (query functions, import in `app/crud/__init__.py`)
4. Create `app/api/routes/<domain>.py` (router, add to `app/api/routes/__init__.py` and mount in `main.py`)
5. Generate and run an Alembic migration

### Authorization & IDOR

Always authorize against a resource's _real_ scope, never a caller-supplied one.
Load the resource first, then check permissions against its actual parent — e.g. load
the task, then require membership on `task.workspace_id`, not on a `workspace_id` taken
from the request. For nested routes like `/workspaces/{workspace_id}/tasks/{task_id}`,
verify the resource's parent matches the path (`task.workspace_id == workspace_id`) and
return **404** on mismatch (not 403 — don't reveal the resource exists in another scope).
This prevents IDOR: a user with rights in one workspace acting on a resource in another.
