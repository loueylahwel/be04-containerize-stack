# BE-04: Containerize Your Stack

Backend AI Engineering — Week 2 Assignment

## What This Is

A FastAPI item service that proves the repository pattern works by swapping between an in-memory store and Postgres with a single environment variable. Docker Compose starts both the app and database together.

## Architecture

```
backend/app/repositories/
├── base.py          # Abstract ItemRepository interface
├── in_memory.py     # Dict-based (data lost on restart)
└── postgres.py      # SQLAlchemy + Postgres (data persists)
```

Routes (`/api/items`) never know which backend is active — they receive the repository via dependency injection from `get_repository()`. Switching storage changes **one env var** and **one file**.

## Quick Start

```bash
# Clone
git clone https://github.com/<your-username>/be04-containerize-stack.git
cd be04-containerize-stack

# Copy env
cp .env.example .env

# Run everything
docker compose up --build
```

The API is at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check (shows which backend is active) |
| POST | `/api/items/` | Create an item |
| GET | `/api/items/` | List all items |
| GET | `/api/items/{id}` | Get one item |
| PUT | `/api/items/{id}` | Update an item |
| DELETE | `/api/items/{id}` | Delete an item |

## Proving Persistence

This is the core of the assignment: data survives restarts when using Postgres.

```bash
# 1. Start the stack
docker compose up --build

# 2. Create some items
curl -X POST http://localhost:8000/api/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Task 1", "description": "Proof of persistence"}'

curl -X POST http://localhost:8000/api/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Task 2", "description": "Survives restart"}'

# 3. Verify they exist
curl http://localhost:8000/api/items/
# Returns both items

# 4. Restart everything (app + database)
docker compose down
docker compose up --build

# 5. Check again — items are still there
curl http://localhost:8000/api/items/
# Returns both items (data persisted in the Postgres volume)
```

**How it works:** The `db_data` Docker volume mounts Postgres data to persistent storage. When containers restart, Postgres re-mounts the same volume, so data is intact.

### Switching to In-Memory

Change `REPO_BACKEND=memory` in `.env`, restart, and see that data **does not** survive:

```bash
# .env
REPO_BACKEND=memory

# Create items, restart, items are gone
docker compose down
docker compose up --build
curl http://localhost:8000/api/items/
# Returns [] — empty
```

## Project Structure

```
.
├── docker-compose.yml        # App + Postgres together
├── .env.example              # Commit this (template)
├── .env                      # Gitignored (real config)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── sql/
│   │   └── init.sql          # Table creation (mounted into Postgres)
│   └── app/
│       ├── main.py           # FastAPI app, repo swap via env var
│       ├── config.py         # Pydantic Settings
│       ├── schemas.py        # Pydantic request/response models
│       ├── routes/
│       │   └── items.py      # CRUD routes (unchanged regardless of repo)
│       └── repositories/
│           ├── base.py       # Abstract interface
│           ├── in_memory.py  # Dict storage
│           └── postgres.py   # Postgres via SQLAlchemy
```

## Key Design Decisions

- **Routes never change:** `items.py` calls `get_repository()` which returns whichever implementation is active
- **SQL init file:** `backend/sql/init.sql` is mounted into Postgres's `/docker-entrypoint-initdb.d/` so the table exists before the app starts
- **Volume for persistence:** `db_data` is a named Docker volume — data survives `docker compose down` but is removed by `docker compose down -v`
- **Health checks:** Postgres has a `pg_isready` healthcheck; the backend waits for it via `depends_on: condition: service_healthy`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Postgres connection string | `postgresql+psycopg2://postgres:postgres@db:5432/items_db` |
| `REPO_BACKEND` | `postgres` or `memory` | `postgres` |
