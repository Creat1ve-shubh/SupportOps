from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import app

client = TestClient(app)


def test_health_without_database():
    assert client.get("/api/health").json()["status"] == "ok"


def test_config_does_not_expose_credentials():
    data = client.get("/api/config").json()
    assert set(data) == {
        "model", "max_tool_calls", "timeout_seconds", "agent_enabled", "mutations_enabled"
    }
    assert data["mutations_enabled"] is False


def test_readiness_reports_database_failure_without_leaking_details(monkeypatch):
    def fail():
        raise OperationalError("private connection details", {}, Exception("secret"))

    monkeypatch.setattr("app.main.get_engine", fail)
    response = client.get("/api/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "offline"}


def test_model_adapter_initializes_without_network():
    from app.agent import build_model

    assert build_model().model_name
