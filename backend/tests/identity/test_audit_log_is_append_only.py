import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session


def _insert_probe(session: Session) -> uuid.UUID:
    entry_id = uuid.uuid4()
    session.execute(
        text(
            "INSERT INTO audit_log (id, action, module, entity_type)"
            " VALUES (:id, 'USER_APPROVED', 'identity', 'user_account')"
        ),
        {"id": entry_id},
    )
    return entry_id


def test_audit_entry_can_be_written(session: Session) -> None:
    entry_id = _insert_probe(session)

    stored = session.execute(
        text("SELECT action FROM audit_log WHERE id = :id"), {"id": entry_id}
    ).scalar_one()

    assert stored == "USER_APPROVED"


def test_audit_entry_cannot_be_updated(session: Session) -> None:
    """ADR-012: a trilha nao pode ser reescrita nem pela role dona da tabela."""
    entry_id = _insert_probe(session)
    session.flush()

    with pytest.raises(DatabaseError, match="append-only"):
        session.execute(
            text("UPDATE audit_log SET action = 'TAMPERED' WHERE id = :id"), {"id": entry_id}
        )


def test_audit_entry_cannot_be_deleted(session: Session) -> None:
    entry_id = _insert_probe(session)
    session.flush()

    with pytest.raises(DatabaseError, match="append-only"):
        session.execute(text("DELETE FROM audit_log WHERE id = :id"), {"id": entry_id})
