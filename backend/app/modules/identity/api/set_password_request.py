from pydantic import BaseModel, Field


class SetPasswordRequest(BaseModel):
    """Senha nova definida pela area de gerenciamento (RN 2.7).

    O minimo de 12 caracteres e o mesmo da criacao de conta. A senha nao volta
    em resposta nenhuma e nao entra na auditoria: a regra proibe que gerentes e
    proprietarios **visualizem** senhas, e definir uma nova nao e ver a antiga."""

    password: str = Field(min_length=12, max_length=256)
