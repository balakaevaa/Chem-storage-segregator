import httpx

LIVE_URL = "https://chem-storage-segregator.onrender.com"

def test_live_health_endpoint():
    """Проверка, что сервер жив и отвечает 200 OK."""
    response = httpx.get(f"{LIVE_URL}/health", timeout=10.0)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_live_analyze_endpoint():
    """Проверка базового флоу классификации реальным POST-запросом."""
    payload = {"queries": ["67-64-1", "7647-01-0"]} # Ацетон и Соляная кислота
    response = httpx.post(f"{LIVE_URL}/api/analyze", json=payload, timeout=15.0)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["chemicals"]) == 2
    assert len(data["matrix"]) == 2