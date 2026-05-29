# Task Management API

A RESTful API for managing tasks, built with **FastAPI**, **SQLAlchemy (async)** and
**PostgreSQL**. Task endpoints are secured with **JWT** authentication.

## Features

- CRUD endpoints for tasks (`/tasks`)
- Pagination, filtering (by title, status, due-date range) on the task list
- JWT authentication with access + refresh tokens
- User registration and login
- All task endpoints require a valid access token

## Tech stack

- Python 3.13, FastAPI, Uvicorn
- SQLAlchemy 2.0 (async) + asyncpg, Alembic migrations
- PostgreSQL 16
- `uv` for dependency management
- Docker / docker-compose

---

## Running with docker-compose

The stack contains two services:

| Service           | Description                              | Port            |
|-------------------|------------------------------------------|-----------------|
| `postgresql`      | PostgreSQL 16 database                    | `5432`          |
| `taskmanagementapi` | The FastAPI app (runs migrations on boot) | `8000`          |

### 1. Create a `.env` file

Both services read their configuration from a `.env` file at the repository root.
Create one with at least the following variables:

```dotenv
# PostgreSQL (used by both the database container and the app)
POSTGRES_USER=dev
POSTGRES_PASSWORD=dev
POSTGRES_DB=dev
POSTGRES_HOST=localhost      # overridden to "postgresql" inside the app container
POSTGRES_PORT=5432

# JWT / security
SECRET_KEY=change-me-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_MINUTES=1440
```

> The `taskmanagementapi` service automatically sets `POSTGRES_HOST=postgresql` so the
> app reaches the database container over the compose network.

### 2. Build and start the stack

```bash
docker compose up --build
```

On startup the API container runs `alembic upgrade head` (see `docker-entrypoint.sh`)
to create the database schema, then starts Uvicorn.

The API is now available at **http://localhost:8000**.

- Interactive docs (Swagger UI): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc

To stop the stack:

```bash
docker compose down          # add -v to also drop the database volume
```

---

## API usage

Base URL: `http://localhost:8000`

### 1. Register a user

`POST /auth/register` — send a JSON body with an email and a password
(8–72 characters).

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "supersecret"}'
```

Response (`201 Created`):

```json
{
  "id": "0f1c9c3e-...-...",
  "email": "alice@example.com",
  "createdAt": "2026-05-30T10:00:00Z"
}
```

### 2. Log in to get a token

`POST /auth/login` — this is an OAuth2 password flow, so the body must be
**form-encoded** (`application/x-www-form-urlencoded`). The `username` field carries
the user's **email**.

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@example.com&password=supersecret"
```

Response (`200 OK`):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

Capture the access token into a shell variable (using `jq`):

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@example.com&password=supersecret" | jq -r .access_token)
```

When the access token expires, exchange the refresh token for a new pair:

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<your-refresh-token>"}'
```

### 3. Call the tasks endpoints (authenticated)

All `/tasks` endpoints require an `Authorization: Bearer <access_token>` header.
Calling them without a valid token returns `401 Unauthorized`.

**List tasks:**

```bash
curl http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN"
```

Response (`200 OK`) — a paginated envelope:

```json
{
  "items": [],
  "total": 0,
  "skip": 0,
  "limit": 1000
}
```

**List with pagination and filters** (all query params are optional):

```bash
# Pagination
curl "http://localhost:8000/tasks?skip=0&limit=20" \
  -H "Authorization: Bearer $TOKEN"

# Filter by status (repeat the param for multiple values)
curl "http://localhost:8000/tasks?status=incomplete&status=complete" \
  -H "Authorization: Bearer $TOKEN"

# Filter by due-date range (ISO 8601)
curl "http://localhost:8000/tasks?due_after=2026-01-01T00:00:00Z&due_before=2026-12-31T00:00:00Z" \
  -H "Authorization: Bearer $TOKEN"
```

**Create a task:**

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Write the README", "description": "Document setup", "dueDate": "2026-06-30T17:00:00Z"}'
```

**Other task endpoints** (all require the `Authorization` header):

| Method   | Path             | Description                   |
|----------|------------------|-------------------------------|
| `GET`    | `/tasks`         | List tasks (paginated)        |
| `POST`   | `/tasks`         | Create a task                 |
| `GET`    | `/tasks/{id}`    | Get a task by id              |
| `PATCH`  | `/tasks/{id}`    | Partially update a task       |
| `DELETE` | `/tasks/{id}`    | Delete a task                 |

> Tip: in the Swagger UI (`/docs`) click **Authorize**, paste the access token, and
> all task requests will include the `Bearer` header automatically.

---

## Local development (without Docker)

Requires [`uv`](https://docs.astral.sh/uv/) and a running PostgreSQL reachable via the
`POSTGRES_*` variables in your `.env`.

```bash
uv sync                       # install dependencies
uv run alembic upgrade head   # apply migrations
uv run uvicorn app.main:app --reload
```

## Running the tests

The integration tests require a PostgreSQL instance (configured via `tests/.env.test`):

```bash
uv run pytest
```