class BusinessRuleError(Exception):
    """A operacao contraria uma regra do dominio.

    Quem pediu tinha alcada; o estado do sistema e que nao permite. Exemplo:
    bloquear o ultimo proprietario ativo (RN 2.5)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
