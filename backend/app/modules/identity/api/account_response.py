import uuid
from decimal import Decimal

from pydantic import BaseModel

from app.modules.identity.infrastructure.models.user_account import UserAccount


class AccountResponse(BaseModel):
    """Conta devolvida ao cliente. Nunca inclui o hash da senha (RN 2.7)."""

    id: uuid.UUID
    email: str
    full_name: str
    artist_name: str | None
    phone: str
    role: str
    acts_as_artist: bool
    status: str
    #: Nulo significa que o artista segue a regra da origem — 70% para cliente
    #: próprio, 50% para indicação do estúdio (ADR-030).
    default_artist_percentage: Decimal | None

    @classmethod
    def from_model(cls, account: UserAccount) -> "AccountResponse":
        return cls(
            id=account.id,
            email=account.email,
            full_name=account.full_name,
            artist_name=account.artist_name,
            phone=account.phone,
            role=str(account.role),
            acts_as_artist=account.acts_as_artist,
            status=str(account.status),
            default_artist_percentage=account.default_artist_percentage,
        )
