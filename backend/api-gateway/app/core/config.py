from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    job_service_url: str = "http://localhost:8001"
    notification_service_url: str = "http://localhost:8002"
    ai_agent_service_url: str = "http://localhost:8003"
    frontend_url: str = "http://localhost:5173"

    environment: str = "development"


settings = Settings()
