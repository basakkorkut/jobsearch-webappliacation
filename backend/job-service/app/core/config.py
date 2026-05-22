import re
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str
    # Get from: Supabase Dashboard > Settings > API > JWT Settings > JWT Secret
    supabase_jwt_secret: str = ""

    # MongoDB
    mongodb_uri: str
    mongodb_db_name: str = "jobsearch"

    # Redis (Upstash REST)
    upstash_redis_rest_url: str
    upstash_redis_rest_token: str

    # RabbitMQ
    rabbitmq_url: str

    # Service URLs
    job_service_url: str = "http://localhost:8001"
    notification_service_url: str = "http://localhost:8002"
    ai_agent_service_url: str = "http://localhost:8003"
    api_gateway_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # General
    environment: str = "development"
    log_level: str = "INFO"

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        # Strip URL-style brackets around password: [pass] → pass
        url = re.sub(r"\[([^\]]+)\]", r"\1", url)
        # Ensure asyncpg driver prefix
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
