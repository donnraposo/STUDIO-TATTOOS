from enum import StrEnum


class QuoteOrigin(StrEnum):
    """Origem do atendimento (RN-CLI-002, RN-REP-001 e RN-REP-002).

    É o campo que decide o dinheiro: cliente do próprio artista divide 70/30,
    indicação do estúdio divide 50/50. Por isso mora no orçamento e não no
    cliente — o mesmo cliente pode voltar pelo artista que o trouxe numa vez e
    ser encaminhado pelo estúdio na seguinte, e cada atendimento tem a sua
    origem (RN-CLI-003)."""

    ARTIST_OWN = "ARTIST_OWN"
    STUDIO_REFERRAL = "STUDIO_REFERRAL"
