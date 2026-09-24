from fastapi.testclient import TestClient


def test_health_reports_process_is_alive(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_reachable_database(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "reachable"}
