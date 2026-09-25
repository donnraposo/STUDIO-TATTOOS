from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Contrato de entrada do login.

    O e-mail e recebido como texto simples de proposito. Validar o formato aqui
    nao acrescentaria seguranca — a busca encontra a conta ou nao — e exigiria a
    dependencia `email-validator` apenas para isso. A unicidade e garantida pela
    coluna CITEXT."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)
