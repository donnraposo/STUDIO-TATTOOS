from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.application import Application
from app.core.container import Container


@pytest.fixture
def container() -> Iterator[Container]:
    Container.reset()
    yield Container.instance()
    Container.reset()


@pytest.fixture
def api_prefix(container: Container) -> str:
    return container.settings.api_prefix


@pytest.fixture
def client(container: Container) -> TestClient:
    return TestClient(Application(container).create())
