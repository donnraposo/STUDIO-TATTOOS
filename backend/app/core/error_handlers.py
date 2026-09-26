from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ErrorHandlers:
    """Traduz erros de dominio em respostas HTTP em um unico lugar.

    Sem isto, cada rota repetiria try/except para converter os mesmos erros — e
    bastaria esquecer um para vazar detalhe interno em uma resposta 500."""

    _STATUS_BY_ERROR = {
        PermissionDeniedError: status.HTTP_403_FORBIDDEN,
        BusinessRuleError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    }

    def register(self, app: FastAPI) -> None:
        for error_type, status_code in self._STATUS_BY_ERROR.items():
            app.add_exception_handler(error_type, self._build_handler(status_code))

    @staticmethod
    def _build_handler(status_code: int):  # noqa: ANN205 - assinatura exigida pelo FastAPI
        def handle(_: Request, exc: Exception) -> JSONResponse:
            return JSONResponse(status_code=status_code, content={"detail": str(exc)})

        return handle
