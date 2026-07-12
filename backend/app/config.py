from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/items_db"
    repo_backend: str = "postgres"

    model_config = {"env_file": ".env"}


settings = Settings()
