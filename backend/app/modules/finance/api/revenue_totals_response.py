from decimal import Decimal

from pydantic import BaseModel

from app.modules.finance.domain.revenue_totals import RevenueTotals


class RevenueTotalsResponse(BaseModel):
    """Os tres numeros do rodape: total tatuado, parte dos artistas e parte da
    casa. Os dois ultimos somam o primeiro, e e assim que o estudio confere."""

    sessions: int
    value: Decimal
    artists: Decimal
    studio: Decimal

    @classmethod
    def from_totals(cls, totals: RevenueTotals) -> "RevenueTotalsResponse":
        return cls(
            sessions=totals.sessions,
            value=totals.value,
            artists=totals.artists,
            studio=totals.studio,
        )
