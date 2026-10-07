from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.shared.errors.booking_conflict_error import BookingConflictError
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ErrorHandlers:
    """Traduz erros de dominio em respostas HTTP em um unico lugar.

    Sem isto, cada rota repetiria try/except para converter os mesmos erros — e
    bastaria esquecer um para vazar detalhe interno em uma resposta 500."""

    _STATUS_BY_ERROR = {
        PermissionDeniedError: status.HTTP_403_FORBIDDEN,
        BusinessRuleError: status.HTTP_422_UNPROCESSABLE_CONTENT,
        BookingConflictError: status.HTTP_409_CONFLICT,
    }

    def register(self, app: FastAPI) -> None:
        for error_type, status_code in self._STATUS_BY_ERROR.items():
            app.add_exception_handler(error_type, self._build_handler(status_code))

    @staticmethod
    def _build_handler(status_code: int):  # noqa: ANN205 - assinatura exigida pelo FastAPI
        def handle(_: Request, exc: Exception) -> JSONResponse:
            return JSONResponse(status_code=status_code, content=ErrorHandlers._body(exc))

        return handle

    @staticmethod
    def _body(exc: Exception) -> dict[str, Any]:
        """Mensagem sempre; campos extras quando o erro tiver o que dizer.

        Um erro de dominio que precise ser tratado de forma propria pela
        interface expoe um dicionario `details` -- e o caso do conflito de
        agenda, que precisa entregar a reserva existente para o modal da
        RN-AGE-007. A extensao e por dados e nao por condicional: nenhum erro
        novo exige tocar neste tradutor."""
        body: dict[str, Any] = {"detail": str(exc)}
        details = getattr(exc, "details", None)
        if isinstance(details, dict):
            body.update(details)
        return body
