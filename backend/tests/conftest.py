from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.application import Application
from app.core.container import Container
from app.core.settings import Settings
from tests.support.database_provisioner import DatabaseProvisioner


@pytest.fixture(scope="session")
def test_database() -> DatabaseProvisioner:
    database = DatabaseProvisioner(Settings(postgres_db="tattoo_studio_test"))
    database.create()
    database.migrate()
    return database


@pytest.fixture
def container(test_database: DatabaseProvisioner, tmp_path: Path) -> Iterator[Container]:
    """Cada teste recebe uma raiz de armazenamento própria.

    O banco é limpo entre testes, mas o sistema de arquivos não se limparia
    sozinho: sem isto, um arquivo gravado por um teste continuaria visível para
    os seguintes, e um teste de contagem de imagens passaria ou falharia conforme
    a ordem de execução."""
    test_database.clear()
    Container.reset()
    settings = test_database.settings.model_copy(
        update={"storage_root": str(tmp_path / "objects")}
    )
    yield Container(settings=settings)
    Container.reset()


@pytest.fixture
def api_prefix(container: Container) -> str:
    return container.settings.api_prefix


@pytest.fixture
def session(container: Container) -> Iterator[Session]:
    with container.database.session() as active_session:
        yield active_session


@pytest.fixture
def client(container: Container) -> TestClient:
    return TestClient(Application(container).create())
