import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import settings
from .routes.items import router as items_router, set_repository
from .routes.summarize import router as summarize_router
from .routes.auth import router as auth_router
from .routes.reports import router as reports_router
from .ai import set_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


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

    if settings.ai_provider == "groq" and settings.groq_api_key:
        from .ai.providers.groq_provider import GroqProvider

        ai = GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)
        set_provider(ai)
        print(f"AI provider: groq ({settings.groq_model})")
    else:
        print("AI provider: none (GROQ_API_KEY not set)")

    yield


app = FastAPI(title="BE-04 Item Service", version="1.0.0", lifespan=lifespan)

app.include_router(items_router)
app.include_router(summarize_router)
app.include_router(auth_router)
app.include_router(reports_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "backend": settings.repo_backend, "ai": settings.ai_provider}
