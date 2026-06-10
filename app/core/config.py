from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # SQL Server connection string
    # Example: mssql+aioodbc://user:pass@host/dbname?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
    DATABASE_URL: str

    # Application
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Rate limiting
    RATE_LIMIT: str = "100/minute"
    REDIS_URL: str | None = None


settings = Settings()
