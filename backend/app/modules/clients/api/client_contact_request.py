from pydantic import BaseModel, Field


class ClientContactRequest(BaseModel):
    """O contato do cliente: o que criar e editar têm em comum (RN-CLI-001).

    Existe como base porque os dois atos tratam dos mesmos três campos, e uma
    lista repetida divergiria no primeiro campo novo — com a chance de esquecer
    justamente o caminho menos usado."""

    name: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=1, max_length=40)
    instagram: str | None = Field(default=None, max_length=80)
