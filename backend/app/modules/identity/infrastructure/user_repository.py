import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

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
