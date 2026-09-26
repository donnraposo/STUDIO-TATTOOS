from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.domain.user_role import UserRole


class AccountManagementPolicy:
    """Quem pode administrar quem (DOCS/01_REGRAS_DE_NEGOCIO.md secao 2).

    Funcao pura de decisao, sem banco nem HTTP, para que a matriz de permissoes
    possa ser lida e testada em um lugar so em vez de espalhada por rotas."""

    _MANAGEABLE_BY_MANAGER = frozenset({UserRole.RESIDENT, UserRole.GUEST})

    def can_create(self, actor: AuthenticatedUser, target_role: UserRole) -> bool:
        if actor.role == UserRole.OWNER:
            return True
        if actor.role == UserRole.MANAGER:
            # O gerente administra residentes e guests, mas nao cria nem promove
            # gerente ou proprietario (RN 2.2 e 2.6).
            return target_role in self._MANAGEABLE_BY_MANAGER
        return False

    def can_change_status(self, actor: AuthenticatedUser, target_role: UserRole) -> bool:
        if actor.role == UserRole.OWNER:
            return True
        if actor.role == UserRole.MANAGER:
            # O gerente nao bloqueia proprietario nem outro gerente (RN 2.5).
            return target_role in self._MANAGEABLE_BY_MANAGER
        return False

    def can_list(self, actor: AuthenticatedUser) -> bool:
        return actor.is_staff
