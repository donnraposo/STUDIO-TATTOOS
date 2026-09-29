from decimal import Decimal

from pydantic import BaseModel, Field


class AdjustSessionsRequest(BaseModel):
    """Novo plano para as sessões que ainda faltam (RN-ORC-006).

    A lista é o valor de **cada** sessão restante, e não um total a dividir: o
    gestor pode querer uma sessão curta e barata seguida de uma longa, e um
    total dividido em partes iguais tiraria dele essa decisão.

    Lista vazia é aceita de propósito — significa que o trabalho acabou onde
    parou, e é um desfecho legítimo de uma sessão interrompida. Nesse caso a
    soma quase sempre difere do total aprovado, e o orçamento volta a pendente,
    que é exatamente o que a regra manda."""

    planned_values: list[Decimal] = Field(default_factory=list, max_length=50)
