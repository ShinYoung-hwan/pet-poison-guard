import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import pytest
import asyncio
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
    # Override the create_task and enqueue dependencies provided by app.api.analyze
    from app.api.analyze import get_create_task_fn, get_enqueue_fn

    async def mock_create_task(input_meta=None):
        return "test-task-id"

    async def mock_enqueue(task_id, file_tuple):
        # do nothing, simulate immediate enqueue
        return None

    app.dependency_overrides[get_create_task_fn] = lambda: mock_create_task
    app.dependency_overrides[get_enqueue_fn] = lambda: mock_enqueue
    img_bytes = b"\x89PNG\r\n\x1a\n"  # PNG header
    resp = client.post("/api/analyze", files={"file": ("test.png", img_bytes, "image/png")})
    assert resp.status_code == 202
    assert "taskId" in resp.json()
    app.dependency_overrides.clear()


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
    from app.api.analyze import get_create_task_fn, get_enqueue_fn

    async def mock_create_task(input_meta=None):
        return "tiny-task-id"

    async def mock_enqueue(task_id, file_tuple):
        return None

    app.dependency_overrides[get_create_task_fn] = lambda: mock_create_task
    app.dependency_overrides[get_enqueue_fn] = lambda: mock_enqueue
    img_bytes = b"\x89PNG\r\n\x1a\n"
    resp = client.post("/api/analyze", files={"file": ("tiny.png", img_bytes, "image/png")})
    assert resp.status_code == 202
    assert "taskId" in resp.json()
    app.dependency_overrides.clear()


def test_analyze_enqueue_fallback_domain_errors(monkeypatch):
    # If enqueue raises AIServiceError or DBServiceError, analyze endpoint should
    # still return 202 and schedule the run_analysis_task via BackgroundTasks.
    from app.api.analyze import get_create_task_fn, get_enqueue_fn, get_run_task_fn
    from app.services.exceptions import AIServiceError, DBServiceError

    async def mock_create_task(input_meta=None):
        return "fallback-domain-task"

    async def mock_enqueue_raises(task_id, file_tuple):
        raise AIServiceError("ai failure")

    # Spy for run_task_fn to record calls
    calls = []

    def spy_run_task(task_id, file_tuple):
        calls.append((task_id, file_tuple))

    app.dependency_overrides[get_create_task_fn] = lambda: mock_create_task
    app.dependency_overrides[get_enqueue_fn] = lambda: mock_enqueue_raises
    app.dependency_overrides[get_run_task_fn] = lambda: spy_run_task

    img_bytes = b"\x89PNG\r\n\x1a\n"
    resp = client.post("/api/analyze", files={"file": ("test.png", img_bytes, "image/png")})
    assert resp.status_code == 202
    # run_task_fn should have been scheduled (BackgroundTasks executes sync functions after response when using TestClient)
    assert len(calls) == 1
    assert calls[0][0] == "fallback-domain-task"

    # Now test DBServiceError behaves the same
    calls.clear()

    async def mock_enqueue_raises_db(task_id, file_tuple):
        raise DBServiceError("db failure")

    app.dependency_overrides[get_enqueue_fn] = lambda: mock_enqueue_raises_db
    resp = client.post("/api/analyze", files={"file": ("test2.png", img_bytes, "image/png")})
    assert resp.status_code == 202
    assert len(calls) == 1
    assert calls[0][0] == "fallback-domain-task"
    app.dependency_overrides.clear()


def test_analyze_enqueue_fallback_generic_exception(monkeypatch):
    # If enqueue raises a generic Exception, analyze endpoint should still
    # return 202 and schedule the run_analysis_task via BackgroundTasks.
    from app.api.analyze import get_create_task_fn, get_enqueue_fn, get_run_task_fn

    async def mock_create_task(input_meta=None):
        return "fallback-generic-task"

    async def mock_enqueue_raises(task_id, file_tuple):
        raise Exception("unexpected")

    # Spy for run_task_fn
    calls = []

    def spy_run_task(task_id, file_tuple):
        calls.append((task_id, file_tuple))

    app.dependency_overrides[get_create_task_fn] = lambda: mock_create_task
    app.dependency_overrides[get_enqueue_fn] = lambda: mock_enqueue_raises
    app.dependency_overrides[get_run_task_fn] = lambda: spy_run_task

    img_bytes = b"\x89PNG\r\n\x1a\n"
    resp = client.post("/api/analyze", files={"file": ("test.png", img_bytes, "image/png")})
    assert resp.status_code == 202
    assert len(calls) == 1
    assert calls[0][0] == "fallback-generic-task"
    app.dependency_overrides.clear()

# Task Status API
def test_get_task_status_success(monkeypatch):
    # 완료된 taskId에 대해 /api/task/{task_id}가 status와 data를 올바르게 반환하는지 검증
    from app.services.task.task_service import create_task, save_task_result
    task_id = asyncio.run(create_task())
    asyncio.run(save_task_result(task_id, [{"name": "chocolate"}]))
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
    from app.services.task.task_service import create_task, update_task_status
    from app.schemas.task import TaskStatus
    task_id = asyncio.run(create_task())
    asyncio.run(update_task_status(task_id, TaskStatus.failed, detail="AI error"))
    resp = client.get(f"/api/task/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"
    assert resp.json()["detail"] == "AI error"
