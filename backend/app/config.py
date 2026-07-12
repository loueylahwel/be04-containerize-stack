from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/items_db"
    repo_backend: str = "postgres"
    ai_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    jwt_secret: str = "change-me-to-a-random-64-char-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    model_config = {"env_file": ".env"}


settings = Settings()
