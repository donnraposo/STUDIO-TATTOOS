from fastapi import APIRouter, Response, status

from app.core.container import Container


class HealthRouter:
    """Expoe as verificacoes de vida e de prontidao do processo."""

    def __init__(self, container: Container) -> None:
        self._container = container

    def build(self) -> APIRouter:
        router = APIRouter(tags=["health"])
        router.add_api_route("/health", self.health, methods=["GET"])
        router.add_api_route("/ready", self.ready, methods=["GET"])
        return router

    def health(self) -> dict[str, str]:
        """Vida do processo. Nao toca o banco, para nao falhar por dependencia externa."""
        return {"status": "ok"}

    def ready(self, response: Response) -> dict[str, str]:
        """Prontidao para receber trafego: exige banco alcancavel."""
        if not self._container.database.is_reachable():
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "unavailable", "database": "unreachable"}
        return {"status": "ready", "database": "reachable"}
