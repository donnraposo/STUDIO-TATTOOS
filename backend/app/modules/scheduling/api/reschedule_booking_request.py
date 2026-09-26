import uuid
from datetime import datetime

from pydantic import BaseModel


class RescheduleBookingRequest(BaseModel):
    """Novo intervalo e, opcionalmente, outra maca (RN-AGE-008)."""

    starts_at: datetime
    ends_at: datetime
    booth_id: uuid.UUID | None = None
