from pydantic import BaseModel, Field


class ClientRequest(BaseModel):
    """Dados do cliente. Nome e telefone obrigatórios, Instagram opcional
    (RN-CLI-001)."""

    name: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=1, max_length=40)
    instagram: str | None = Field(default=None, max_length=80)
