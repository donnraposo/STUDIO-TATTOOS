from fastapi import FastAPI

from app.core.container import Container
from app.modules.health.api.health_router import HealthRouter
from app.modules.identity.api.auth_router import AuthRouter


class Application:
    """Monta a aplicacao FastAPI a partir do container, registrando os
    roteadores de cada modulo de negocio."""

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
        for router in self._routers():
            app.include_router(router, prefix=settings.api_prefix)
        return app

    def _routers(self) -> list:
        return [
            HealthRouter(self._container).build(),
            AuthRouter(self._container).build(),
        ]
