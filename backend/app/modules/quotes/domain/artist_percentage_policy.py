from decimal import Decimal

from app.modules.quotes.domain.quote_origin import QuoteOrigin


class ArtistPercentagePolicy:
    """Percentual do artista conforme a origem do atendimento.

    Cliente próprio fica com 70% para o artista (RN-REP-001); indicação do
    estúdio divide ao meio (RN-REP-002).

    É um mapa e não uma cadeia de `if`: acrescentar uma origem no futuro passa a
    ser uma linha de dados, e não uma condicional nova espalhada por quem
    calcula repasse. O percentual devolvido aqui é apenas o **padrão vigente** —
    a partir da aprovação, o que vale é a cópia congelada no orçamento
    (RN-REP-006), e mudar estes números não alcança trabalho já aprovado."""

    _BY_ORIGIN: dict[QuoteOrigin, Decimal] = {
        QuoteOrigin.ARTIST_OWN: Decimal("70.00"),
        QuoteOrigin.STUDIO_REFERRAL: Decimal("50.00"),
    }

    def for_origin(self, origin: QuoteOrigin) -> Decimal:
        return self._BY_ORIGIN[origin]
