import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.identity.infrastructure.models.user_session import UserSession


class SessionRepository:
    """Sessoes vivem no servidor (ADR-003), o que permite revoga-las na hora.

    Uma sessao so e valida enquanto nao foi revogada e nenhum dos dois prazos
    venceu: inatividade e limite absoluto."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        user_id: uuid.UUID,
        idle_minutes: int,
        absolute_hours: int,
        ip_address: str | None,
        user_agent: str | None,
    ) -> UserSession:
        now = datetime.now(UTC)
        record = UserSession(
            user_id=user_id,
            idle_expires_at=now + timedelta(minutes=idle_minutes),
            absolute_expires_at=now + timedelta(hours=absolute_hours),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(record)
        self._session.flush()
        return record

    def find_valid(self, session_id: uuid.UUID) -> UserSession | None:
        now = datetime.now(UTC)
        statement = select(UserSession).where(
            UserSession.id == session_id,
            UserSession.revoked_at.is_(None),
            UserSession.idle_expires_at > now,
            UserSession.absolute_expires_at > now,
        )
        return self._session.execute(statement).scalar_one_or_none()

    def extend_idle_window(self, record: UserSession, idle_minutes: int) -> None:
        now = datetime.now(UTC)
        record.last_seen_at = now
        record.idle_expires_at = now + timedelta(minutes=idle_minutes)
        self._session.flush()

    def revoke(self, session_id: uuid.UUID) -> None:
        self._session.execute(
            update(UserSession)
            .where(UserSession.id == session_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )

    def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Usado no bloqueio de conta e na troca de senha (RN 2.7)."""
        result = self._session.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        return result.rowcount
