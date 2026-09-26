from pydantic import BaseModel, Field


class CancelBookingRequest(BaseModel):
    """Cancelamento ou não comparecimento (RN-AGE-009 e RN-AGE-010)."""

    reason: str = Field(min_length=1, max_length=200)
    no_show: bool = False
