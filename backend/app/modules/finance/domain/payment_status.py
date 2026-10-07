from enum import StrEnum


class PaymentStatus(StrEnum):
    """Estados do pagamento (RN-PAG-007).

    O fluxo é `Informado → Confirmado ou Recusado → Devolvido ou Estornado`.

    **Nenhum deles apaga o lançamento.** A regra é explícita: um pagamento nunca
    será apagado, e correção entra como ajuste vinculado ao registro original.
    Por isso `REFUNDED` é um estado e não a ausência da linha — quem devolveu
    precisa continuar aparecendo no histórico, com quanto e por quê.

    `CHARGED_BACK` é o estorno pela operadora, que chega de fora e não é uma
    decisão do estúdio."""

    REPORTED = "REPORTED"
    CONFIRMED = "CONFIRMED"
    REFUSED = "REFUSED"
    REFUNDED = "REFUNDED"
    CHARGED_BACK = "CHARGED_BACK"
