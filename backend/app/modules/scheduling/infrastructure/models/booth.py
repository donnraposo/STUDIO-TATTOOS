import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm_base import OrmBase


class Booth(OrmBase):
    """Maca. Maca e bancada formam um único recurso reservável (RN-AGE-001).

    O estúdio começa com quatro; gerente e proprietário podem acrescentar."""

    __tablename__ = "booth"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
