# BE-04: Containerize Your Stack + W4: AI API + W5: Auth

Backend AI Engineering — Week 2, 4 & 5 Assignments

## What This Is

A FastAPI service with three features:
1. **Repository pattern** — swap between in-memory and Postgres with one env var (W2)
2. **AI summarization** — call Groq's LLM API, get structured JSON back, log costs (W4)
3. **JWT authentication** — register, login, protected routes with hashed passwords (W5)

## Architecture

```
backend/app/repositories/
├── base.py          # Abstract ItemRepository interface
├── in_memory.py     # Dict-based (data lost on restart)
└── postgres.py      # SQLAlchemy + Postgres (data persists)
```

Routes (`/api/items`) never know which backend is active — they receive the repository via dependency injection from `get_repository()`. Switching storage changes **one env var** and **one file**.

## AI Provider Seam

```
backend/app/ai/
├── providers/
│   ├── base.py            # Abstract AIProvider interface
│   └── groq_provider.py   # Groq (free tier, no card)
├── client.py              # Single seam — summarize() calls the LLM here
├── schemas.py             # Pydantic output validation (SummarizeOutput)
└── cost.py                # Token cost estimation from public pricing
```

Every AI call goes through `ai.client.summarize()`. The provider is injected at startup based on `AI_PROVIDER` env var. Switching providers touches **only the providers/ directory**.

## Authentication (W5)

```
backend/app/auth/
├── passwords.py      # bcrypt hash + verify
├── jwt.py            # JWT create + decode
└── dependencies.py   # get_current_user dependency
```

- **Passwords** hashed with bcrypt (passlib). Never stored in plaintext.
- **JWT tokens** issued on login, verified on protected routes.
- **Protected route:** `POST /api/summarize` requires `Authorization: Bearer <token>` header.
- **Honest responses:** 401 for missing/invalid tokens, 409 for duplicate email/username.

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
| POST | `/api/auth/register` | Register a new user (email, username, password) |
| POST | `/api/auth/login` | Login, returns JWT token |
| GET | `/api/auth/me` | Get current user (requires token) |
| POST | `/api/summarize` | Summarize text into 3 bullet points (AI-powered, requires token) |

## Testing Auth

```bash
# 1. Register
curl -X POST http://localhost:8050/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","username":"you","password":"secret123"}'

# 2. Login (returns JWT)
curl -X POST http://localhost:8050/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret123"}'
# → {"access_token":"eyJ...","token_type":"bearer"}

# 3. Get current user
curl http://localhost:8050/api/auth/me \
  -H "Authorization: Bearer eyJ..."

# 4. Call protected route (summarize)
curl -X POST http://localhost:8050/api/summarize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{"text": "Your text to summarize here."}'

# 5. Without token → 401
curl -X POST http://localhost:8050/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "This will fail."}'
# → {"detail":"Not authenticated"}
```

## Testing the AI Feature

```bash
# Summarize a block of text
curl -X POST http://localhost:8050/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Docker is a platform for developing, shipping, and running applications in containers. Containers are lightweight, portable, and self-sufficient. Docker Compose is a tool for defining and running multi-container applications."}'
```

Response:
```json
{
  "title": "Docker Overview",
  "bullets": [
    "Docker is a platform for developing, shipping, and running applications in containers.",
    "Docker Compose is a tool for defining and running multi-container Docker applications.",
    "Containers are lightweight, portable, and self-sufficient."
  ]
}
```

Server logs show cost per call:
```
ai INFO summarize | provider=groq model=llama-3.1-8b-instant in=220 out=67 cost=$0.016360
```

### Reliability Features

- **Structured output:** Response validated against Pydantic schema. Malformed JSON → retry once with correction prompt.
- **Timeouts:** 30s timeout on every LLM call.
- **Smart retries:** 429 (rate limit) and 5xx (server error) retry with exponential backoff. 400 errors never retried.
- **Cost logging:** Every call logs provider, model, input/output tokens, and estimated cost in USD.

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
│       ├── main.py           # FastAPI app, repo + AI provider swap via env vars
│       ├── config.py         # Pydantic Settings
│       ├── schemas.py        # Pydantic request/response models
│       ├── routes/
│       │   ├── items.py      # CRUD routes (unchanged regardless of repo)
│       │   ├── auth.py       # Register, login, /me
│       │   └── summarize.py  # POST /summarize — AI-powered (protected)
│       ├── auth/
│       │   ├── passwords.py  # bcrypt hash/verify
│       │   ├── jwt.py        # JWT create/decode
│       │   └── dependencies.py # get_current_user
│       ├── repositories/
│       │   ├── base.py       # Abstract interface
│       │   ├── in_memory.py  # Dict storage
│       │   └── postgres.py   # Postgres via SQLAlchemy
│       └── ai/
│           ├── client.py     # summarize() — the single AI seam
│           ├── schemas.py    # SummarizeOutput (Pydantic validation)
│           ├── cost.py       # Token cost estimation
│           └── providers/
│               ├── base.py        # Abstract AIProvider interface
│               └── groq_provider.py # Groq implementation
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
| `AI_PROVIDER` | LLM provider | `groq` |
| `GROQ_API_KEY` | Groq API key (free, no card) | — |
| `GROQ_MODEL` | Groq model to use | `llama-3.1-8b-instant` |
| `JWT_SECRET` | Secret key for JWT signing | `change-me-to-a-random-64-char-string` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token expiry in minutes | `60` |
