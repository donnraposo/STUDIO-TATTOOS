import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.domain.user_status import UserStatus


class UserAccount(OrmBase):
    """Conta de acesso. Proprietario e gerente podem tambem atuar como
    tatuadores, caso em que o nome artistico e obrigatorio (RN 2.8).

    Estados e perfis sao gravados como texto com restricao CHECK em vez de tipo
    ENUM nativo: acrescentar um valor nas proximas sprints passa a ser uma
    alteracao de restricao, sem ALTER TYPE."""

    __tablename__ = "user_account"
    __table_args__ = (
        CheckConstraint(
            "role IN ('OWNER', 'MANAGER', 'RESIDENT', 'GUEST')",
            name="ck_user_account_role",
        ),
        CheckConstraint(
            "status IN ('PENDING_APPROVAL', 'ACTIVE', 'BLOCKED', 'REJECTED')",
            name="ck_user_account_status",
        ),
        CheckConstraint(
            "NOT (acts_as_artist OR role IN ('RESIDENT', 'GUEST')) OR artist_name IS NOT NULL",
            name="ck_user_account_artist_name_required",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(CITEXT(), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    artist_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(16), nullable=False)
    acts_as_artist: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[UserStatus] = mapped_column(String(24), nullable=False)
    requested_role: Mapped[UserRole | None] = mapped_column(String(16), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_account.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
