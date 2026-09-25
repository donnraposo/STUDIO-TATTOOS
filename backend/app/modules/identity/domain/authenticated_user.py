import uuid
from dataclasses import dataclass

from app.modules.identity.domain.user_role import UserRole


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identidade resolvida a partir da sessao, repassada aos casos de uso.

    Imutavel e sem acesso ao ORM de proposito: a camada de aplicacao decide
    autorizacao a partir destes dados, sem poder alterar a conta por engano."""

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    acts_as_artist: bool

    @property
    def is_staff(self) -> bool:
        """Proprietario e gerente concentram as decisoes administrativas."""
        return self.role in (UserRole.OWNER, UserRole.MANAGER)

    @property
    def tattoos(self) -> bool:
        """Quem possui agenda e repasse proprios (RN 2)."""
        return self.role in (UserRole.RESIDENT, UserRole.GUEST) or self.acts_as_artist
