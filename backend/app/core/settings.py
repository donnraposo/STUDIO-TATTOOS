from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracao da aplicacao, lida do ambiente. Nenhum segredo em codigo."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Tattoo Studio API"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    debug: bool = False

    studio_timezone: str = "Europe/Dublin"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "tattoo_studio"
    postgres_user: str = "tattoo_studio"
    postgres_password: str = "tattoo_studio"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
