from pydantic import BaseModel, Field

from app.modules.identity.domain.user_role import UserRole


class UpdateAccountRequest(BaseModel):
    """Contrato de edicao de conta pela area de gerenciamento (RN 2.6).

    **Sem senha, de proposito.** Trocar senha encerra as sessoes da conta
    (RN 2.7) e e ato de outra natureza; aceito aqui, o gestor derrubaria alguem
    ao corrigir um telefone.

    **Sem `status`.** Bloquear e desbloquear tem rotas proprias, que registram
    motivo e encerram sessoes -- mudar o estado por este campo pularia as duas
    coisas."""

    email: str = Field(min_length=3, max_length=320)
    full_name: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=1, max_length=40)
    role: UserRole
    acts_as_artist: bool = False
    artist_name: str | None = Field(default=None, max_length=160)
