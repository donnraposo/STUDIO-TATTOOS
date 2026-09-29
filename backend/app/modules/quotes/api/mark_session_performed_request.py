from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MarkSessionPerformedRequest(BaseModel):
    """Registro de que a sessão aconteceu (RN-ORC-005 e RN-ORC-006).

    `charged_value` ausente significa sessão inteira. Informado, é o que foi
    efetivamente cobrado numa sessão interrompida, e é ele que passa a ser a
    base do repasse daquela sessão.

    `performed_at` é opcional e a data real da sessão, não a agendada. Existe
    porque o registro costuma ser feito depois — no fim do expediente, ou no dia
    seguinte — e é dela que sai o vencimento do pós-venda (RN-POS-001)."""

    performed_at: datetime | None = None
    charged_value: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
