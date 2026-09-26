import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.modules.reporting.infrastructure.models.audit_log import AuditLog


class AuditRecorder:
    """Grava a trilha de auditoria (RN 10.7).

    Escreve na mesma transacao do caso de uso: se a operacao for desfeita, o
    registro tambem some, e nunca fica um rastro de algo que nao aconteceu.
    Uma vez efetivada, a linha nao pode mais ser alterada (ADR-012)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        actor_id: uuid.UUID | None,
        action: str,
        module: str,
        entity_type: str,
        entity_id: str | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> None:
        self._session.add(
            AuditLog(
                actor_id=actor_id,
                action=action,
                module=module,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
                reason=reason,
            )
        )
        self._session.flush()
