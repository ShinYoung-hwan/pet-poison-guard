
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_analyze_image_invalid_type():
    resp = client.post("/analyze", files={"file": ("test.txt", b"notanimage", "text/plain")})
    assert resp.status_code == 400
    assert "Only image files" in resp.json()["detail"]

def test_analyze_image_too_large(monkeypatch):
    # Patch httpx.AsyncClient to not actually call AI server
    monkeypatch.setattr("httpx.AsyncClient.post", lambda *a, **k: type("Resp", (), {"raise_for_status": lambda s: None, "json": lambda s: {"dummy": True}})())
    big = b"0" * (5 * 1024 * 1024 + 1)
    resp = client.post("/analyze", files={"file": ("big.jpg", big, "image/jpeg")})
    assert resp.status_code == 413
    assert "File too large" in resp.json()["detail"]
