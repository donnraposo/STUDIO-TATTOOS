from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracao da aplicacao, lida do ambiente. Nenhum segredo em codigo."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Tattoo Studio API"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    debug: bool = False

    studio_timezone: str = "Europe/Dublin"

    # Sessao: DOCS/03_REQUISITOS_NAO_FUNCIONAIS.md secao 3.
    session_cookie_name: str = "studio_session"
    csrf_cookie_name: str = "studio_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    session_idle_minutes: int = 60
    session_absolute_hours: int = 12

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "tattoo_studio"
    postgres_user: str = "tattoo_studio"
    postgres_password: str = "tattoo_studio"

    @property
    def cookies_require_https(self) -> bool:
        """Em producao o cookie so trafega por HTTPS. Em desenvolvimento o
        navegador precisa aceita-lo em http://localhost."""
        return self.environment.lower() == "production"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
