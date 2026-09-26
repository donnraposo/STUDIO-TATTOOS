class PermissionDeniedError(Exception):
    """O ator autenticado nao tem alcada para a operacao.

    Distinta de erro de regra de negocio: aqui a operacao seria valida, mas nao
    para quem a pediu."""

    def __init__(self, message: str = "Not allowed.") -> None:
        super().__init__(message)
        self.message = message
