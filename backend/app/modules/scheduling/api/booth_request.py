from pydantic import BaseModel, Field


class BoothRequest(BaseModel):
    """A numeração é atribuída pelo sistema; o rótulo é livre."""

    label: str | None = Field(default=None, max_length=80)
