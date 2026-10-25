# Notes API

A REST API for notes, built with **FastAPI** and **SQLite**. It uses **JWT** authentication and **role-based access control** (Admin, User, Viewer).

## Features

- Register and log in; the login returns a JWT bearer token
- Notes with a `title` and `content`, each owned by the user who created it
- Three roles with different permissions (see below)
- Consistent `401`, `403`, `404` errors, plus `409` and `422`
- Automated tests with pytest, using an in-memory database
- Interactive docs at `/docs` (Swagger UI)

## Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/) for dependency management

## Setup

```bash
# 1. Install dependencies (creates .venv automatically)
uv sync

# 2. Create your environment file
cp .env.example .env            # Windows: Copy-Item .env.example .env

# 3. Generate a secret key and paste it into .env as SECRET_KEY
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

### Configuration (`.env`)

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Key used to sign JWTs. **Required**, no default. | none |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `30` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./notes.db` |

Never commit `.env`. It is already in `.gitignore`.

## Running

# Create demo accounts (safe to run more than once)
uv run python -m app.seed

# Start the server
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for Swagger UI. Click **Authorize** to log in.

### Demo accounts (local development only)

| Username | Password | Role |
|---|---|---|
| `admin` | `admin12345` | admin |
| `alice` | `alice12345` | user |
| `victor` | `victor12345` | viewer |

These passwords are for local testing only. Do not use them in production.

## Roles and permissions

| Action | Admin | User | Viewer |
|---|:---:|:---:|:---:|
| Read notes | yes | yes | yes |
| Create a note | yes | yes | no (403) |
| Edit or delete own note | yes | yes | no (403) |
| Edit or delete any note | yes | no (403) | no (403) |

- `POST /auth/register` always creates a **user**. Nobody can sign up as admin.
- Admin and viewer accounts are created with `app/seed.py` or directly in the database.
- All logged-in roles can read all notes.

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | none | Health check |
| POST | `/auth/register` | none | Create a user account |
| POST | `/auth/login` | none | Log in (form data), returns a JWT |
| GET | `/auth/me` | any role | Show the current user |
| GET | `/notes` | any role | List notes (`skip`, `limit` query params) |
| GET | `/notes/{id}` | any role | Get one note |
| POST | `/notes` | admin, user | Create a note |
| PUT | `/notes/{id}` | admin, or owner | Update title and/or content |
| DELETE | `/notes/{id}` | admin, or owner | Delete a note |

### Example with curl

```bash
# Log in (form data, not JSON)
curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=alice&password=alice12345"

# Create a note
curl -X POST http://127.0.0.1:8000/notes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello", "content": "World"}'
```

On Windows PowerShell, use `curl.exe` instead of `curl`.

## Error codes

| Code | Meaning | Example |
|---|---|---|
| 401 | Missing, invalid, or expired token; wrong login | Calling `/notes` without a token |
| 403 | Logged in but not allowed | Viewer creating a note; user editing someone else's note |
| 404 | Resource does not exist | `GET /notes/999` |
| 409 | Conflict | Registering a username that already exists |
| 422 | Validation error | Empty title, password shorter than 8 characters |

Checks run in this order: authentication (401), role (403), note lookup (404), ownership (403). A viewer who tries to edit a missing note gets 403, not 404.

## Testing

```bash
uv run pytest -v
```

Tests use an in-memory SQLite database, so your real `notes.db` is never touched.

- `tests/test_auth.py`: registration, login, token handling (invalid, expired, deleted user)
- `tests/test_notes.py`: role and ownership rules, plus 401, 403, 404, and 422 cases

## Project structure

```
notes-api/
├── app/
│   ├── main.py          # App creation, router registration, table creation
│   ├── config.py        # Settings loaded from .env
│   ├── database.py      # Engine, session, get_db dependency
│   ├── models.py        # User and Note tables, Role enum
│   ├── schemas.py       # Pydantic request/response models
│   ├── security.py      # Password hashing, JWT create/decode
│   ├── deps.py          # get_current_user, require_roles
│   ├── seed.py          # Demo accounts for each role
│   └── routers/
│       ├── auth.py      # /auth endpoints
│       └── notes.py     # /notes endpoints and permission rules
├── tests/
│   ├── conftest.py      # Test database and user fixtures
│   ├── test_auth.py
│   └── test_notes.py
├── pyproject.toml
├── uv.lock
├── .env.example
└── README.md
```

## Design notes

- **The token stores only the user id.** The role is read from the database on every request, so role changes take effect immediately.
- **Passwords** are hashed with bcrypt. Passwords are limited to 72 characters because bcrypt ignores anything longer.
- **Login errors are identical** for an unknown user and a wrong password, so attackers cannot discover which usernames exist.
- **`PUT` is a partial update:** only the fields you send are changed, and explicit `null` values are ignored.
- **Tables are created on startup** with `create_all`. A larger project would use Alembic migrations.

## Possible improvements

- Alembic migrations
- Refresh tokens and logout/revocation
- An admin endpoint to change user roles
- Search and filtering on `GET /notes`
- Docker setup