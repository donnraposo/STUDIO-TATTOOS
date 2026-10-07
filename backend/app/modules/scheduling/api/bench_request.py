from pydantic import BaseModel, Field


class BenchRequest(BaseModel):
    """A numeração é atribuída pelo sistema; o rótulo é livre."""

    label: str | None = Field(default=None, max_length=80)
