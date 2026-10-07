import uuid

from pydantic import BaseModel

from app.modules.scheduling.infrastructure.models.bench import Bench


class BenchResponse(BaseModel):
    """Maca. Maca e bancada são um único recurso reservável (RN-AGE-001)."""

    id: uuid.UUID
    number: int
    label: str | None
    active: bool

    @classmethod
    def from_model(cls, bench: Bench) -> "BenchResponse":
        return cls(
            id=bench.id, number=bench.number, label=bench.label, active=bench.active
        )
