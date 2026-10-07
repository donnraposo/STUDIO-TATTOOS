from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.modules.finance.domain.payment_method import PaymentMethod


class RefundPaymentRequest(BaseModel):
    """Registro de uma devolucao ja realizada (RN-PAG-009).

    `method` e proprio e nao herdado: a forma da devolucao pode diferir da forma
    do pagamento original, e a regra preve isso explicitamente."""

    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    method: PaymentMethod
    reason: str = Field(min_length=3, max_length=500)
    note: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=1000)
    ] = None
