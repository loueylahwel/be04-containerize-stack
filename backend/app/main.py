import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import settings
from .routes.items import router as items_router, set_repository


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.repo_backend == "postgres":
        from .repositories.postgres import PostgresItemRepository, Base

        repo = PostgresItemRepository(settings.database_url)

        for attempt in range(10):
            try:
                Base.metadata.create_all(repo._engine)
                print(f"Postgres connected on attempt {attempt + 1}")
                break
            except Exception as e:
                print(f"Waiting for Postgres (attempt {attempt + 1}/10): {e}")
                time.sleep(2)
        else:
            raise RuntimeError("Could not connect to Postgres after 10 attempts")
    else:
        from .repositories.in_memory import InMemoryItemRepository

        repo = InMemoryItemRepository()
        print("Using in-memory repository")

    set_repository(repo)
    yield


app = FastAPI(title="BE-04 Item Service", version="1.0.0", lifespan=lifespan)

app.include_router(items_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "backend": settings.repo_backend}
