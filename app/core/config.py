from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/shadchan"
    firebase_credentials_path: str | None = None
    groq_api_key: str | None = None
    # must support response_format=json_schema - see
    # https://console.groq.com/docs/structured-outputs#supported-models
    groq_model: str = "openai/gpt-oss-120b"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
