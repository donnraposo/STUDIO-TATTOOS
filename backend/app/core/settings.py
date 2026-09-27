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

    # Armazenamento privado de arquivos (ADR-006, revisto na M4.3). Volume
    # nomeado do Docker, fora do sistema de arquivos efemero da imagem.
    storage_root: str = "/var/lib/tattoo-studio/objects"

    # Limites das imagens de referencia do orcamento (RN-ORC-004). Ficam aqui, e
    # nao no codigo, porque sao operacionais: o estudio muda sem nova versao.
    reference_image_max_bytes: int = 10 * 1024 * 1024
    reference_image_allowed_types: str = "image/jpeg,image/png,image/webp"
    reference_image_max_per_quote: int = 10

    @property
    def cookies_require_https(self) -> bool:
        """Em producao o cookie so trafega por HTTPS. Em desenvolvimento o
        navegador precisa aceita-lo em http://localhost."""
        return self.environment.lower() == "production"

    @property
    def allowed_reference_image_types(self) -> frozenset[str]:
        """Lista separada por virgula no ambiente, conjunto no codigo.

        Variavel de ambiente e texto; exigir JSON para uma lista de tres tipos
        atrapalharia quem edita o `.env` sem ganhar nada."""
        return frozenset(
            entry.strip().lower()
            for entry in self.reference_image_allowed_types.split(",")
            if entry.strip()
        )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
