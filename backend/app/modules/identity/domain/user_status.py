from enum import StrEnum


class UserStatus(StrEnum):
    """Estados da conta. PENDING_APPROVAL nao concede acesso as areas internas
    (RN 2.6); BLOCKED preserva historico e encerra sessoes (RN 2.5)."""

    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
