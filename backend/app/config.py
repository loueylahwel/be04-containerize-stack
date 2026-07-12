from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/items_db"
    repo_backend: str = "postgres"
    ai_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    model_config = {"env_file": ".env"}


settings = Settings()
