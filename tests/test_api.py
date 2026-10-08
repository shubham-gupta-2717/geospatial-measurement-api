from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_file_returns_404():
    response = client.get("/api/files/does-not-exist/")
    assert response.status_code == 404
