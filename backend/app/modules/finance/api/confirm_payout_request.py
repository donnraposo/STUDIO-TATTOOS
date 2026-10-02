from typing import Annotated

from pydantic import BaseModel, StringConstraints


class ConfirmPayoutRequest(BaseModel):
    """Confirmacao da transferencia ao artista (RN-REP-004 e RN-REP-007).

    O comprovante e opcional: a regra o preve como anexo possivel, e exigi-lo
    impediria registrar um repasse pago em dinheiro."""

    receipt_object_key: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=500)
    ] = None
