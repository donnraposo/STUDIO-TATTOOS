import uuid

from app.modules.identity.domain.account_management_policy import AccountManagementPolicy
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.identity.infrastructure.status_history_repository import (
    StatusHistoryRepository,
)
from app.modules.identity.infrastructure.user_repository import UserRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class UpdateAccount:
    """Edita o cadastro de uma conta (RN 2.1, 2.2 e 2.6).

    A regra autoriza desde sempre -- *"gerente ou proprietario pode autorizar,
    **editar** ou bloquear cadastros de residentes e guests"* --, e ate aqui so
    existiam criar e bloquear. Corrigir um telefone exigia o banco.

    **Mudar de perfil e so do proprietario, e e literal.** A RN 2.6 diz que *"o
    gerente nao pode promover usuarios **nem alterar perfis de acesso**"* -- as
    duas coisas, e nao so a promocao. Trocar residente por guest tambem e
    alterar perfil de acesso: muda a exigencia de sinal (RN-GST-004) e o repasse
    de quem o estudio indica.

    Checado pelo perfil do ator e nao pela politica de criacao: `can_create`
    diria que o gerente pode criar residentes e guests -- verdade -- e com isso
    deixaria passar a troca entre os dois, que a regra proibe.

    **O ultimo proprietario ativo nao perde o perfil.** Rebaixa-lo deixaria o
    estudio sem quem cria proprietario, e sem volta. E a mesma garantia da RN
    2.5 para o bloqueio, pela outra porta: bloquear e rebaixar esvaziam a
    administracao do mesmo jeito.

    **Artista precisa de nome de artista.** O banco recusa o contrario, e tirar
    o nome de quem tatua -- ou promover a tatuador quem nao tem nome -- deixaria
    o cadastro impossivel de gravar.

    **A senha nao passa por aqui.** Trocar senha encerra as sessoes da conta
    (RN 2.7) e e ato de outra natureza; misturado a edicao de telefone, o gestor
    derrubaria alguem sem querer.

    A edicao fica no historico e na auditoria, como a RN 2.6 exige."""

    def __init__(
        self,
        users: UserRepository,
        history: StatusHistoryRepository,
        policy: AccountManagementPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._users = users
        self._history = history
        self._policy = policy
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        account_id: uuid.UUID,
        full_name: str,
        phone: str,
        email: str,
        role: UserRole,
        acts_as_artist: bool,
        artist_name: str | None = None,
    ) -> UserAccount:
        account = self._users.find_by_id(account_id)
        if account is None:
            raise BusinessRuleError("Account not found.")

        current_role = UserRole(account.role)
        if not self._policy.can_change_status(actor, current_role):
            raise PermissionDeniedError("You cannot edit this account.")

        self._guard_role_change(actor, account, current_role, role)
        self._guard_artist_name(role, acts_as_artist, artist_name)

        normalized_email = email.strip()
        changed_email = normalized_email.lower() != account.email.lower()
        if changed_email and self._users.exists_with_email(normalized_email):
            raise BusinessRuleError("This email is already registered.")

        previous = {
            "email": account.email,
            "full_name": account.full_name,
            "artist_name": account.artist_name,
            "phone": account.phone,
            "role": str(account.role),
            "acts_as_artist": account.acts_as_artist,
        }

        account.email = normalized_email
        account.full_name = full_name.strip()
        account.phone = phone.strip()
        account.artist_name = artist_name.strip() if artist_name else None
        account.role = role
        account.acts_as_artist = acts_as_artist
        self._users.add(account)

        if current_role != role:
            self._history.record(
                user_id=account.id,
                from_status=str(account.status),
                to_status=str(account.status),
                reason="ROLE_CHANGED",
                note=f"{current_role} -> {role}",
                actor_id=actor.id,
            )

        self._audit.record(
            actor_id=actor.id,
            action="ACCOUNT_UPDATED",
            module="identity",
            entity_type="user_account",
            entity_id=str(account.id),
            old_values=previous,
            new_values={
                "email": account.email,
                "full_name": account.full_name,
                "artist_name": account.artist_name,
                "phone": account.phone,
                "role": str(role),
                "acts_as_artist": acts_as_artist,
            },
        )
        return account

    def _guard_role_change(
        self,
        actor: AuthenticatedUser,
        account: UserAccount,
        current_role: UserRole,
        role: UserRole,
    ) -> None:
        if current_role == role:
            return
        if actor.role != UserRole.OWNER:
            raise PermissionDeniedError(
                "Only the owner can change the role of an account."
            )
        if not self._policy.can_create(actor, role):
            raise PermissionDeniedError("You cannot give this account that role.")
        if current_role == UserRole.OWNER and self._users.count_active_owners(
            excluding=account.id
        ) == 0:
            raise BusinessRuleError(
                "The last active owner cannot lose the role; the studio would be left "
                "without administration."
            )

    @staticmethod
    def _guard_artist_name(
        role: UserRole, acts_as_artist: bool, artist_name: str | None
    ) -> None:
        tattoos = acts_as_artist or role in (UserRole.RESIDENT, UserRole.GUEST)
        if tattoos and not artist_name:
            raise BusinessRuleError("An artist name is required for someone who tattoos.")
