from fastapi.testclient import TestClient

from app.application import Application
from app.core.container import Container
from app.core.settings import Settings


def test_ready_reports_unavailable_when_database_is_unreachable() -> None:
    """Prontidao deve falhar quando o banco nao responde, para que o proxy
    nao encaminhe trafego a uma instancia incapaz de atender."""
    settings = Settings(postgres_host="unreachable-host", postgres_port=1)
    container = Container(settings=settings)
    client = TestClient(Application(container).create())

    response = client.get(f"{settings.api_prefix}/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unreachable"}
