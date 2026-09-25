import uuid

from app.modules.identity.infrastructure.session_repository import SessionRepository


class EndSession:
    """Encerra a sessao corrente. Idempotente: encerrar duas vezes nao e erro."""

    def __init__(self, sessions: SessionRepository) -> None:
        self._sessions = sessions

    def execute(self, session_id: uuid.UUID) -> None:
        self._sessions.revoke(session_id)
