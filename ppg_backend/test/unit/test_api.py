import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Health API
def test_health_success():
    """
    시나리오: 서비스의 상태 확인용 헬스 체크 엔드포인트(`/api/health`)가
    정상적인 서비스 상태를 반환하는지 검증한다.

    절차:
    1. `/api/health`에 GET 요청을 보낸다.
    2. HTTP 응답 코드가 200인지 확인한다.
    3. 응답 바디에 `{"status": "ok"}` 형태의 JSON이 포함되어 있는지 확인한다.

    예상 결과: 상태 코드 200 및 간단한 정상 상태 JSON을 반환한다.
    에지케이스: 서비스 초기화 실패나 의존 서비스(데이터베이스/AI 등) 문제 시
    헬스 엔드포인트의 반환값이 변경될 수 있으며, 해당 경우 테스트는 실패해야 한다.
    """
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

# Analyze API
def test_analyze_image_success(monkeypatch):
    """
    시나리오: 정상적인 이미지 파일을 업로드했을 때 분석 작업이 정상 등록되고
    `taskId`를 반환하는지 검증한다. 외부 의존(enqueue, create_task)은 모킹한다.

    절차:
    1. `create_task`와 `enqueue` 의존성을 모킹하여 외부 효과를 제거한다.
    2. 작은 PNG 헤더 바이트를 포함하는 파일로 `/api/analyze`에 POST 요청을 보낸다.
    3. 응답 코드가 202(accepted)인지, 응답 JSON에 `taskId`가 포함되는지 확인한다.

    예상 결과: 202 응답과 함께 `taskId`가 반환되며, enqueue 호출이 문제를 일으키지 않아야 한다.
    에지케이스: enqueue가 예외를 던지면 fallback 경로로 BackgroundTasks가 예약되는지 다른 테스트에서 검증한다.
    """
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
    """
    시나리오: 이미지가 아닌 파일(.txt 등)을 업로드했을 때 입력 검증에 의해 거부되는지 검증한다.

    절차:
    1. `text/plain` 타입 파일을 `/api/analyze`로 POST한다.
    2. 응답 코드가 400이며, 상세 메시지에 지원되는 파일 형식 관련 메시지가 포함되는지 확인한다.

    예상 결과: 400 응답과 적절한 에러 메시지(예: "Only image files")를 반환한다.
    """
    resp = client.post("/api/analyze", files={"file": ("test.txt", b"abc", "text/plain")})
    assert resp.status_code == 400
    assert "Only image files" in resp.json()["detail"]


def test_analyze_image_too_large():
    """
    시나리오: 허용된 최대 업로드 크기(예: 5MB)를 초과한 파일 업로드가 적절히 거부되는지 검증한다.

    절차:
    1. 5MB보다 큰 바이트 배열을 생성하여 `/api/analyze`에 POST한다.
    2. 응답 코드가 413(Payload Too Large) 또는 적절한 4xx로 거부되는지 확인한다.
    3. 에러 메시지가 파일 크기 초과 관련 내용을 포함하는지 확인한다.

    예상 결과: 413 응답과 파일 크기 초과에 대한 상세 메시지를 반환한다.
    """
    big = b"0" * (5 * 1024 * 1024 + 1)
    resp = client.post("/api/analyze", files={"file": ("big.jpg", big, "image/jpeg")})
    assert resp.status_code == 413
    assert "File too large" in resp.json()["detail"]


def test_analyze_image_edge_case_min_size(monkeypatch):
    """
    시나리오: 매우 작은(최소 크기) 이미지 업로드가 정상적으로 처리되는지 검증하는 엣지케이스 테스트.

    절차:
    1. `create_task`와 `enqueue`를 모킹한다.
    2. 최소한의 PNG 헤더 바이트를 가진 파일을 업로드한다.
    3. 202 응답 및 `taskId` 포함 여부를 확인한다.

    예상 결과: 최소 크기의 이미지도 유효 파일로 인식되어 작업이 등록되고 `taskId`가 반환되어야 한다.
    """
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
    """
    시나리오: `enqueue` 호출이 도메인 예외(AIServiceError 또는 DBServiceError)를 던질 때,
    API가 여전히 202를 반환하고 BackgroundTasks로 대체 실행(fallback)을 예약하는지 검증한다.

    절차:
    1. `create_task`는 정상적으로 task_id를 반환하도록 모킹한다.
    2. `enqueue`는 AIServiceError 또는 DBServiceError를 던지도록 모킹한다.
    3. `run_task_fn`(fallback 함수)을 스파이로 대체하여 호출 기록을 수집한다.
    4. `/api/analyze`를 호출하고 202 응답 및 run_task_fn이 호출되었는지 확인한다.

    예상 결과: enqueue 실패 시에도 202을 반환하고, fallback 함수가 호출되어 작업이 예약되어야 한다.
    """
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
    """
    시나리오: `enqueue`가 일반 예외(Exception)를 던질 때에도 API가 202를 반환하고
    BackgroundTasks로 대체 실행을 예약하는지 검증한다(도메인 예외 외 일반 예외 처리).

    절차:
    1. `create_task`를 모킹해 정상 task_id 반환.
    2. `enqueue`는 일반 Exception을 던지도록 모킹.
    3. `run_task_fn`을 스파이로 대체하고 호출 여부 확인.
    4. `/api/analyze` 호출 시 202 응답 및 fallback 호출 확인.

    예상 결과: 일반 예외 발생 시에도 서비스는 작업을 최종적으로 예약하려고 시도해야 하며,
    API는 실패 대신 수용(202)을 반환한다.
    """
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
    """
    시나리오: 완료된 태스크에 대해 상태 조회(`/api/task/{task_id}`)가 올바른 상태와 결과를 반환하는지 검증한다.

    절차:
    1. `create_task`로 새로운 task_id를 생성한다.
    2. `save_task_result`로 해당 태스크에 결과를 저장하고 상태를 완료로 마크한다.
    3. `/api/task/{task_id}`로 GET 요청을 보내 상태와 data 필드를 확인한다.

    예상 결과: 200 응답, `status`는 `completed`, `data`는 저장된 결과와 일치해야 한다.
    """
    from app.services.task.task_service import create_task, save_task_result
    task_id = asyncio.run(create_task())
    asyncio.run(save_task_result(task_id, [{"name": "chocolate"}]))
    resp = client.get(f"/api/task/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["data"] == [{"name": "chocolate"}]


def test_get_task_status_not_found():
    """
    시나리오: 존재하지 않는 task_id로 상태 조회 요청 시 404 에러와 적절한 메시지를 반환하는지 검증한다.

    절차:
    1. 임의의 존재하지 않는 ID로 `/api/task/{id}`를 호출한다.
    2. 응답 코드와 메시지를 확인한다.

    예상 결과: 404 응답과 `Task not found` 관련 상세 메시지를 반환한다.
    """
    resp = client.get("/api/task/doesnotexist")
    assert resp.status_code == 404
    assert "Task not found" in resp.json()["detail"]


def test_get_task_status_failed(monkeypatch):
    """
    시나리오: 실패 상태(failed)로 마크된 태스크의 상태 조회 시 `status`와 `detail` 필드가 올바르게 반환되는지 검증한다.

    절차:
    1. `create_task`로 task_id를 생성한다.
    2. `update_task_status`를 호출해 해당 태스크를 failed 상태로 설정하고 `detail`을 저장한다.
    3. `/api/task/{task_id}`로 GET 요청해 status와 detail이 기대값과 일치하는지 확인한다.

    예상 결과: 200 응답, `status`가 `failed`, `detail`이 설정한 에러 메시지와 일치한다.
    """
    from app.services.task.task_service import create_task, update_task_status
    from app.schemas.task import TaskStatus
    task_id = asyncio.run(create_task())
    asyncio.run(update_task_status(task_id, TaskStatus.failed, detail="AI error"))
    resp = client.get(f"/api/task/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"
    assert resp.json()["detail"] == "AI error"
