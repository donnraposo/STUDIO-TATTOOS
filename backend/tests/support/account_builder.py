from sqlalchemy.orm import Session

from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.identity.infrastructure.password_hasher import PasswordHasher


class AccountBuilder:
    """Cria contas para os testes sem repetir o preenchimento em cada cenario."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._hasher = PasswordHasher()

    def create(
        self,
        email: str = "owner@studio.ie",
        password: str = "correct horse battery staple",
        role: UserRole = UserRole.OWNER,
        status: UserStatus = UserStatus.ACTIVE,
        acts_as_artist: bool = False,
    ) -> UserAccount:
        account = UserAccount(
            email=email,
            password_hash=self._hasher.hash(password),
            full_name="Studio Owner",
            artist_name="Ink"
            if acts_as_artist or role in (UserRole.RESIDENT, UserRole.GUEST)
            else None,
            phone="+353 1 000 0000",
            role=role,
            status=status,
            acts_as_artist=acts_as_artist,
        )
        self._session.add(account)
        self._session.flush()
        return account
