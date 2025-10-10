import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Health API
def test_health_success():
    # /api/health 엔드포인트가 정상적으로 서비스 상태를 반환하는지 검증
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

# Analyze API
def test_analyze_image_success(monkeypatch):
    # 정상적인 이미지 파일 업로드 시 /api/analyze가 성공적으로 taskId를 반환하는지 검증
    def mock_request_ai_analysis(file_tuple, timeout=15.0, top_k=10):
        return [{"name": "chocolate", "image": "img.png", "description": "toxic"}]
    monkeypatch.setattr("app.services.ai_service.request_ai_analysis", mock_request_ai_analysis)
    img_bytes = b"\x89PNG\r\n\x1a\n"  # PNG header
    resp = client.post("/api/analyze", files={"file": ("test.png", img_bytes, "image/png")})
    assert resp.status_code == 202
    assert "taskId" in resp.json()


def test_analyze_image_invalid_type():
    # 이미지가 아닌 파일 업로드 시 /api/analyze가 400 에러와 적절한 메시지를 반환하는지 검증
    resp = client.post("/api/analyze", files={"file": ("test.txt", b"abc", "text/plain")})
    assert resp.status_code == 400
    assert "Only image files" in resp.json()["detail"]


def test_analyze_image_too_large():
    # 5MB를 초과하는 이미지 업로드 시 /api/analyze가 413 에러와 적절한 메시지를 반환하는지 검증
    big = b"0" * (5 * 1024 * 1024 + 1)
    resp = client.post("/api/analyze", files={"file": ("big.jpg", big, "image/jpeg")})
    assert resp.status_code == 413
    assert "File too large" in resp.json()["detail"]


def test_analyze_image_edge_case_min_size(monkeypatch):
    # 최소 크기의 유효 이미지 업로드 시 /api/analyze가 정상적으로 동작하는지 검증 (엣지 케이스)
    def mock_request_ai_analysis(file_tuple, timeout=15.0, top_k=10):
        return []
    monkeypatch.setattr("app.services.ai_service.request_ai_analysis", mock_request_ai_analysis)
    img_bytes = b"\x89PNG\r\n\x1a\n"
    resp = client.post("/api/analyze", files={"file": ("tiny.png", img_bytes, "image/png")})
    assert resp.status_code == 202
    assert "taskId" in resp.json()

# Task Status API
def test_get_task_status_success(monkeypatch):
    # 완료된 taskId에 대해 /api/task/{task_id}가 status와 data를 올바르게 반환하는지 검증
    from app.services.task_service import create_task, set_task_completed
    task_id = create_task()
    set_task_completed(task_id, [{"name": "chocolate"}])
    resp = client.get(f"/api/task/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["data"] == [{"name": "chocolate"}]


def test_get_task_status_not_found():
    # 존재하지 않는 taskId에 대해 /api/task/{task_id}가 404 에러와 적절한 메시지를 반환하는지 검증
    resp = client.get("/api/task/doesnotexist")
    assert resp.status_code == 404
    assert "Task not found" in resp.json()["detail"]


def test_get_task_status_failed(monkeypatch):
    # 실패 상태의 taskId에 대해 /api/task/{task_id}가 status와 detail을 올바르게 반환하는지 검증
    from app.services.task_service import create_task, set_task_failed
    task_id = create_task()
    set_task_failed(task_id, "AI error")
    resp = client.get(f"/api/task/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"
    assert resp.json()["detail"] == "AI error"
