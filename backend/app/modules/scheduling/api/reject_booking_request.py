from pydantic import BaseModel, Field

from app.modules.scheduling.domain.rejection_reason import RejectionReason


class RejectBookingRequest(BaseModel):
    """Recusa com motivo de lista fechada (RN-AGE-006); observação é opcional."""

    reason: RejectionReason
    note: str | None = Field(default=None, max_length=500)
