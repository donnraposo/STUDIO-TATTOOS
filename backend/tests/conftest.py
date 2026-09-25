from collections.abc import Iterator

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
def container(test_database: DatabaseProvisioner) -> Iterator[Container]:
    test_database.clear()
    Container.reset()
    yield Container(settings=test_database.settings)
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
