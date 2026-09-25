import uuid

from pydantic import BaseModel

from app.modules.identity.domain.authenticated_user import AuthenticatedUser


class CurrentUserResponse(BaseModel):
    """Identidade devolvida ao cliente. Nunca inclui hash de senha nem o
    identificador da sessao."""

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    acts_as_artist: bool

    @classmethod
    def from_domain(cls, user: AuthenticatedUser) -> "CurrentUserResponse":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=str(user.role),
            acts_as_artist=user.acts_as_artist,
        )
