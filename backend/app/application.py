from fastapi import APIRouter, FastAPI

from app.core.container import Container
from app.core.error_handlers import ErrorHandlers
from app.modules.health.api.health_router import HealthRouter
from app.modules.identity.api.account_router import AccountRouter
from app.modules.identity.api.auth_router import AuthRouter


class Application:
    """Monta a aplicacao FastAPI a partir do container, registrando os
    roteadores de cada modulo de negocio e a traducao de erros de dominio."""

    def __init__(self, container: Container) -> None:
        self._container = container

    def create(self) -> FastAPI:
        settings = self._container.settings
        app = FastAPI(
            title=settings.app_name,
            version="0.1.0",
            docs_url=f"{settings.api_prefix}/docs",
            openapi_url=f"{settings.api_prefix}/openapi.json",
        )
        ErrorHandlers().register(app)
        for router in self._routers():
            app.include_router(router, prefix=settings.api_prefix)
        return app

    def _routers(self) -> list[APIRouter]:
        return [
            HealthRouter(self._container).build(),
            AuthRouter(self._container).build(),
            AccountRouter(self._container).build(),
        ]
