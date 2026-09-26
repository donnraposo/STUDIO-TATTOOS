import uuid

from pydantic import BaseModel

from app.modules.scheduling.infrastructure.models.booth import Booth


class BoothResponse(BaseModel):
    """Maca. Maca e bancada são um único recurso reservável (RN-AGE-001)."""

    id: uuid.UUID
    number: int
    label: str | None
    active: bool

    @classmethod
    def from_model(cls, booth: Booth) -> "BoothResponse":
        return cls(
            id=booth.id, number=booth.number, label=booth.label, active=booth.active
        )
