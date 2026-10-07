from decimal import Decimal

from pydantic import BaseModel, Field


class ArtistPercentageRequest(BaseModel):
    """O acordo de percentual de um artista (ADR-030).

    **Nulo e omitido significam a mesma coisa aqui, e de propósito:** devolver o
    artista à regra da origem. É assim que um acordo é encerrado, e um campo
    obrigatório obrigaria a inventar um número para dizer "nenhum".

    Só decide o que a **próxima** aprovação vai congelar. Trabalho já aprovado
    carrega a cópia feita no momento em que foi acordado (RN-REP-006)."""

    percentage: Decimal | None = Field(default=None, gt=0, le=100, max_digits=5, decimal_places=2)
