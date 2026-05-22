import re
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    mongodb_uri: str
    mongodb_db_name: str = "jobsearch"
    rabbitmq_url: str
    environment: str = "development"
    log_level: str = "INFO"

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        url = re.sub(r"\[([^\]]+)\]", r"\1", url)   # strip [password] brackets
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
