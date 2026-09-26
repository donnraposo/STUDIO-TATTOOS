import uuid

from sqlalchemy.orm import Session

from app.modules.identity.infrastructure.models.user_status_history import UserStatusHistory


class StatusHistoryRepository:
    """Rastro de mudanca de estado da conta (RN 2.5 e 2.6).

    Separado da auditoria geral de proposito: este historico e consultado junto
    da conta, enquanto `audit_log` serve a trilha transversal do sistema."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        user_id: uuid.UUID,
        from_status: str | None,
        to_status: str,
        actor_id: uuid.UUID | None,
        reason: str | None = None,
        note: str | None = None,
    ) -> None:
        self._session.add(
            UserStatusHistory(
                user_id=user_id,
                from_status=from_status,
                to_status=to_status,
                reason=reason,
                note=note,
                actor_id=actor_id,
            )
        )
        self._session.flush()
