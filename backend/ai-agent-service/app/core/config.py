from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LM Studio
    lm_studio_url: str = "http://localhost:1234"
    lm_studio_model: str = "qwen3-5b"

    # Internal service URLs
    job_service_url: str = "http://localhost:8001"

    # General
    environment: str = "development"
    log_level: str = "INFO"


settings = Settings()
