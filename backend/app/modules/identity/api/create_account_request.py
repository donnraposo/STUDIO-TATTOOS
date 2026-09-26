from pydantic import BaseModel, Field

from app.modules.identity.domain.user_role import UserRole


class CreateAccountRequest(BaseModel):
    """Contrato de criacao de conta pela area de gerenciamento.

    Se o perfil pode criar o papel pedido e decidido pela politica de dominio,
    nao aqui: validacao de formato e autorizacao sao responsabilidades distintas."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)
    full_name: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=1, max_length=40)
    role: UserRole
    acts_as_artist: bool = False
    artist_name: str | None = Field(default=None, max_length=160)
