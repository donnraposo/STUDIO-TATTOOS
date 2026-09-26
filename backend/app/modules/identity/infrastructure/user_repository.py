import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.models.user_account import UserAccount


class UserRepository:
    """Acesso a contas. O e-mail e comparado sem diferenciar maiusculas porque
    a coluna e CITEXT."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_email(self, email: str) -> UserAccount | None:
        statement = select(UserAccount).where(UserAccount.email == email.strip())
        return self._session.execute(statement).scalar_one_or_none()

    def find_by_id(self, user_id: uuid.UUID) -> UserAccount | None:
        return self._session.get(UserAccount, user_id)

    def add(self, account: UserAccount) -> UserAccount:
        self._session.add(account)
        self._session.flush()
        return account

    def list_all(self) -> list[UserAccount]:
        statement = select(UserAccount).order_by(UserAccount.full_name)
        return list(self._session.execute(statement).scalars())

    def count_active_owners(self, excluding: uuid.UUID | None = None) -> int:
        """Sustenta a regra de nao deixar o estudio sem administracao (RN 2.5).

        A contagem roda com FOR UPDATE para que dois bloqueios simultaneos nao
        leiam "dois proprietarios ativos" ao mesmo tempo e removam ambos."""
        statement = select(UserAccount.id).where(
            UserAccount.role == UserRole.OWNER,
            UserAccount.status == UserStatus.ACTIVE,
        )
        if excluding is not None:
            statement = statement.where(UserAccount.id != excluding)
        return len(list(self._session.execute(statement.with_for_update()).scalars()))

    def exists_with_email(self, email: str) -> bool:
        statement = select(func.count()).select_from(UserAccount).where(
            UserAccount.email == email.strip()
        )
        return bool(self._session.execute(statement).scalar_one())
