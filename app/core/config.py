from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/shadchan"
    firebase_credentials_path: str | None = None
    groq_api_key: str | None = None
    # must support response_format=json_schema - see
    # https://console.groq.com/docs/structured-outputs#supported-models
    groq_model: str = "openai/gpt-oss-120b"

    b2_endpoint_url: str | None = None
    b2_region: str = "us-west-002"
    b2_key_id: str | None = None
    b2_application_key: str | None = None
    b2_bucket_name: str | None = None
    b2_upload_url_expires_in: int = 300
    b2_read_url_expires_in: int = 3600

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
