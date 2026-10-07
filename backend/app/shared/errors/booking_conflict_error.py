class BookingConflictError(Exception):
    """O intervalo pedido colide com um agendamento existente.

    Separado de `BusinessRuleError` porque a interface precisa reagir de forma
    própria: a RN-AGE-007 exige um modal que mostre o agendamento conflitante e
    **não permita ignorar o conflito**. Por isso carrega o escopo — se o choque
    foi na maca ou na agenda do artista — e o agendamento existente."""

    def __init__(self, scope: str, message: str, conflicting_booking_id: str | None = None) -> None:
        super().__init__(message)
        self.scope = scope
        self.message = message
        self.conflicting_booking_id = conflicting_booking_id

    @property
    def details(self) -> dict[str, str | None]:
        """O que a resposta HTTP precisa levar alem da mensagem.

        Sem isto o modal da RN-AGE-007 nao teria o que mostrar: ele exige
        apresentar a reserva existente, e um texto de erro nao permite abrir o
        agendamento conflitante nem destaca-lo na agenda."""
        return {"scope": self.scope, "conflicting_booking_id": self.conflicting_booking_id}
