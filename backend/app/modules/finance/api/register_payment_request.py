import uuid
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.modules.finance.domain.payment_kind import PaymentKind
from app.modules.finance.domain.payment_method import PaymentMethod


class RegisterPaymentRequest(BaseModel):
    """Lancamento de um recebimento informado (RN-PAG-002 e RN-PAG-006).

    Nao traz `status`: pagamento nasce sempre em `REPORTED`, e aceitar o estado
    de fora permitiria lancar um recebimento ja confirmado, pulando a
    conferencia que a RN-PAG-002 exige do gestor.

    `booking_id` e `session_id` sao exclusivos, e a checagem fica no caso de uso
    porque depende do tipo: sinal pertence ao agendamento (RN-PAG-001), saldo
    pertence a sessao (RN-PAG-008)."""

    booking_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    kind: PaymentKind
    method: PaymentMethod
    note: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=1000)
    ] = None
