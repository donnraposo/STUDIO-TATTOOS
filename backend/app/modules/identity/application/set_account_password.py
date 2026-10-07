import uuid

from app.modules.identity.domain.account_management_policy import AccountManagementPolicy
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.identity.infrastructure.password_hasher import PasswordHasher
from app.modules.identity.infrastructure.session_repository import SessionRepository
from app.modules.identity.infrastructure.user_repository import UserRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class SetAccountPassword:
    """Define uma senha nova para uma conta (RN 2.7).

    **Definir nao e visualizar.** A regra proibe que gerentes e proprietarios
    **vejam** senhas, e nada aqui as mostra: o banco guarda hash, o campo da
    tela nasce vazio, e o valor nao entra na auditoria nem no historico. O que a
    gestao pode e dar uma senha nova a quem perdeu a dela.

    **Encerra as sessoes da conta, e e o ponto da regra.** Uma senha trocada sem
    encerrar sessao deixaria em pe exatamente o acesso que a troca queria
    cortar -- quem estivesse logado continuaria dentro com a senha antiga ja
    invalida.

    A regra fala em encerrar *as demais* sessoes, o que protege quem troca a
    propria senha num fluxo de autoatendimento. Aqui e outra coisa: um terceiro
    redefine a senha de alguem, e a leitura segura e encerrar **todas** as
    sessoes daquela conta. Quem redefinir a propria por esta tela sai junto, o
    que custa um login e nao deixa brecha.

    Caso de uso separado do `UpdateAccount` de proposito: corrigir um telefone e
    derrubar as sessoes de alguem sao atos de naturezas diferentes, e juntos num
    unico `salvar` o gestor faria o segundo sem querer."""

    #: O mesmo minimo da criacao de conta. Repetido como constante e nao
    #: herdado do schema porque a regra e de dominio, e o schema e borda.
    MINIMUM_LENGTH = 12

    def __init__(
        self,
        users: UserRepository,
        sessions: SessionRepository,
        hasher: PasswordHasher,
        policy: AccountManagementPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._hasher = hasher
        self._policy = policy
        self._audit = audit

    def execute(
        self, actor: AuthenticatedUser, account_id: uuid.UUID, password: str
    ) -> UserAccount:
        account = self._users.find_by_id(account_id)
        if account is None:
            raise BusinessRuleError("Account not found.")

        if not self._policy.can_change_status(actor, UserRole(account.role)):
            raise PermissionDeniedError("You cannot set the password of this account.")

        if len(password) < SetAccountPassword.MINIMUM_LENGTH:
            raise BusinessRuleError(
                f"A password needs at least {SetAccountPassword.MINIMUM_LENGTH} characters."
            )

        account.password_hash = self._hasher.hash(password)
        self._users.add(account)

        # Na mesma transacao que grava o hash: se o commit falhar, a senha
        # antiga continua valendo e as sessoes tambem.
        revoked = self._sessions.revoke_all_for_user(account.id)

        # Sem valores: a senha nao entra no registro, nem a antiga nem a nova.
        self._audit.record(
            actor_id=actor.id,
            action="ACCOUNT_PASSWORD_SET",
            module="identity",
            entity_type="user_account",
            entity_id=str(account.id),
            new_values={"revoked_sessions": revoked},
        )
        return account
