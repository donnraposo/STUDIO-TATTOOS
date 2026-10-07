from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


class ConfirmSessionPaymentRequest(BaseModel):
    """Confirmação do valor recebido (RN-ORC-005).

    Ambos os campos são opcionais no esquema e condicionais na regra: omitido o
    valor, vale o que o artista informou; informado um valor diferente, o motivo
    passa a ser obrigatório. A condição mora no caso de uso e não aqui, porque
    depende do que está gravado na sessão — um esquema não tem como saber."""

    charged_value: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    reason: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=500)
    ] = None
