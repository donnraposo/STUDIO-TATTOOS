from app.modules.finance.domain.payment_status import PaymentStatus


class PaymentTransition:
    """Quais mudanças de estado o pagamento aceita (RN-PAG-007).

    O fluxo da regra é `Informado → Confirmado ou Recusado → Devolvido ou
    Estornado`, e está escrito aqui como **mapa de dados**, não como cadeia de
    `if` espalhada pelos casos de uso. Acrescentar um estado passa a ser uma
    linha; espalhado, seria uma condicional nova em cada lugar que decide, com a
    chance de esquecer um deles justamente no caminho menos usado.

    Decisão pura: não conhece banco, ator nem transação. É só a pergunta "deste
    estado dá para chegar naquele"."""

    _ALLOWED: dict[PaymentStatus, frozenset[PaymentStatus]] = {
        PaymentStatus.REPORTED: frozenset({PaymentStatus.CONFIRMED, PaymentStatus.REFUSED}),
        PaymentStatus.CONFIRMED: frozenset(
            {PaymentStatus.REFUNDED, PaymentStatus.CHARGED_BACK}
        ),
        PaymentStatus.REFUSED: frozenset(),
        PaymentStatus.REFUNDED: frozenset(),
        PaymentStatus.CHARGED_BACK: frozenset(),
    }

    def allows(self, current: PaymentStatus, target: PaymentStatus) -> bool:
        return target in self._ALLOWED[current]

    def is_final(self, current: PaymentStatus) -> bool:
        """Recusado, devolvido e estornado não vão a lugar nenhum. Um pagamento
        recusado que voltasse a confirmado apagaria a recusa do histórico, e é
        justamente isso que a RN-PAG-007 proíbe ao mandar corrigir por ajuste."""
        return not self._ALLOWED[current]
