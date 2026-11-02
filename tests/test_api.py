from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_endpoint_with_demo_reagents():
    payload = {
        "queries": ["67-64-1", "7647-01-0", "1310-73-2", "7697-37-2"]
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["chemicals"]) == 4
    assert len(data["matrix"]) == 4
    assert len(data["cabinets"]) >= 3
    assert len(data["conflicts"]) >= 2