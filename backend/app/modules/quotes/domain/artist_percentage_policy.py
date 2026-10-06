from decimal import Decimal

from app.modules.quotes.domain.quote_origin import QuoteOrigin


class ArtistPercentagePolicy:
    """Percentual do artista conforme a origem do atendimento.

    Cliente próprio fica com 70% para o artista (RN-REP-001); indicação do
    estúdio divide ao meio (RN-REP-002).

    É um mapa e não uma cadeia de `if`: acrescentar uma origem no futuro passa a
    ser uma linha de dados, e não uma condicional nova espalhada por quem
    calcula repasse.

    **Estes são os percentuais de quem não tem acordo próprio.** Desde 06/10/2026
    o estúdio registra percentual por artista, e ele vence esta tabela — a
    decisão está no ADR-030. A RN-REP-001 e a RN-REP-002 continuam como estão no
    documento de regras, e cabe ao responsável atualizá-las.

    O percentual devolvido aqui é apenas o **padrão vigente** —
    a partir da aprovação, o que vale é a cópia congelada no orçamento
    (RN-REP-006), e mudar estes números não alcança trabalho já aprovado."""

    _BY_ORIGIN: dict[QuoteOrigin, Decimal] = {
        QuoteOrigin.ARTIST_OWN: Decimal("70.00"),
        QuoteOrigin.STUDIO_REFERRAL: Decimal("50.00"),
    }

    def for_origin(self, origin: QuoteOrigin, artist_default: Decimal | None = None) -> Decimal:
        """O acordo do artista vence a regra da origem, quando existe.

        O estúdio negocia percentuais próprios — a planilha de controle mostra
        85% ao lado dos 70% e dos 50% no mesmo mês. Tratar isso como exceção no
        código obrigaria uma versão nova do sistema a cada acordo novo; tratado
        como dado, é o gestor quem ajusta.

        **Nulo cai na regra da origem**, que continua valendo para a maioria."""
        if artist_default is not None:
            return artist_default
        return self._BY_ORIGIN[origin]
