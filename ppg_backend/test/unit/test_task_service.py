import asyncio
import pytest
from app.services.task.task_service import (
    InMemoryTaskStore,
    create_task,
    get_task,
    update_task_status,
    save_task_result,
    increment_retries,
    list_tasks,
    cleanup_tasks,
    set_default_store,
    reset_default_store,
)
from app.schemas.task import TaskStatus


# Helper to run async functions in tests
def run(coro):
    # Use asyncio.run which creates and closes an event loop safely
    return asyncio.run(coro)


def test_inmemory_create_get_update_save_and_wrappers():
    """
    시나리오: InMemoryTaskStore를 사용해 태스크 생성(create), 조회(get), 상태 업데이트(update), 결과 저장(save), 재시도 증가(increment_retries), 목록 조회(list), 정리(cleanup) 등의 전형적인 워크플로우를 검증한다.

    절차:
    1. 새로운 `InMemoryTaskStore` 인스턴스를 생성하고 기본 스토어로 설정한다.
    2. `create_task`를 호출해 task_id를 얻는다.
    3. `get_task`로 생성된 태스크의 상태와 메타(input_meta), 타임스탬프(created_at/updated_at)를 확인한다.
    4. `update_task_status`로 상태를 `running`으로 변경하고 반영되는지 확인한다.
    5. `save_task_result`로 결과를 저장하고 상태가 `completed`로 변경되는지 확인한다.
    6. `increment_retries` 호출로 재시도 카운터가 정상적으로 증가하는지 확인한다.
    7. `list_tasks`로 태스크가 나열되는지 확인하고, `cleanup_tasks`로 오래된 태스크 정리 호출 후 반환값을 확인한다.

    예상 결과:
    - 모든 호출은 타입과 반환값에 대해 예상 범위를 만족한다.
    - 상태 전이(pending -> running -> completed)가 올바르게 반영된다.
    - 타임스탬프는 수치이며 생성/갱신 시간이 유효하다.
    - 재시도 카운터는 정수이며 0 이상의 값을 반환한다.

    에지케이스:
    - cleanup_tasks(0)은 현재 시점보다 이전의 항목만 제거하므로 0 이상의 정수(0 가능)를 반환한다.
    """
    # Use a fresh store for isolation
    store = InMemoryTaskStore()
    set_default_store(store)

    # create_task (wrapper)
    task_id = run(create_task({"filename": "food.jpg"}))
    assert isinstance(task_id, str) and len(task_id) > 0

    # get_task
    task = run(get_task(task_id))
    assert task is not None
    assert task["status"] == TaskStatus.pending
    assert task["input_meta"]["filename"] == "food.jpg"
    # new canonical timestamps should be numeric epoch seconds
    assert "created_at" in task and isinstance(task["created_at"], (int, float))
    assert "updated_at" in task and isinstance(task["updated_at"], (int, float))
    assert task["created_at"] > 0 and task["updated_at"] > 0

    # update_task_status -> mark running
    ok = run(update_task_status(task_id, TaskStatus.running))
    assert ok is True
    task = run(get_task(task_id))
    assert task["status"] == TaskStatus.running

    # save_task_result -> mark completed
    result_payload = [{"name": "chocolate", "toxic": True}]
    ok = run(save_task_result(task_id, result_payload))
    assert ok is True
    task = run(get_task(task_id))
    assert task["status"] == TaskStatus.completed
    assert task["result"] == result_payload
    # timestamps updated and numeric
    assert isinstance(task["updated_at"], (int, float))

    # increment_retries on existing task
    retries = run(increment_retries(task_id))
    assert isinstance(retries, int) and retries >= 0

    # list_tasks contains our task
    all_tasks = run(list_tasks())
    assert task_id in all_tasks

    # cleanup_tasks with 0 seconds should remove tasks older than now -> none
    removed = run(cleanup_tasks(0))
    assert isinstance(removed, int) and removed >= 0

    # reset default store to not affect other tests
    reset_default_store()


def test_nonexistent_task_updates_and_increment():
    """
    시나리오: 존재하지 않는 task_id에 대한 상태 업데이트와 재시도 증가 요청의 실패 동작을 검증한다.

    절차:
    1. 새로운 `InMemoryTaskStore`를 생성하고 기본 스토어로 설정한다.
    2. `update_task_status`에 존재하지 않는 task_id를 전달하고 False를 반환하는지 확인한다.
    3. `increment_retries`에 존재하지 않는 task_id를 전달하면 -1을 반환하는지 확인한다.

    예상 결과:
    - 비존재 태스크에 대한 업데이트는 실패(False)를 반환한다.
    - 재시도 증가 요청은 실패를 나타내는 -1을 반환한다.

    에지케이스:
    - 내부 스토어가 비어있는 초기 상태에서도 동일한 실패 동작을 보장해야 한다.
    """
    store = InMemoryTaskStore()
    set_default_store(store)

    # update non-existent task
    ok = run(update_task_status("nope", TaskStatus.failed, detail="not found"))
    assert ok is False

    # increment retries on non-existent task returns -1
    r = run(increment_retries("nope"))
    assert r == -1

    reset_default_store()


def test_validation_errors_and_cleanup_args():
    """
    시나리오: API/서비스 레벨의 입력 검증과 경계값(음수 인자) 처리 로직을 검증한다.

    절차:
    1. 새로운 `InMemoryTaskStore`를 생성하고 기본 스토어로 설정한다.
    2. 정상적인 `create_task` 호출로 태스크를 하나 생성한다(기본 경로 확인).
    3. `get_task`에 비문자열(예: 123)을 전달하여 TypeError 발생을 확인한다.
    4. `update_task_status`에 비문자열 task_id를 전달하여 TypeError 발생을 확인한다.
    5. `cleanup_tasks`에 음수 값을 전달하여 ValueError가 발생하는지 확인한다.

    예상 결과:
    - 잘못된 타입 인자에 대해 TypeError가 발생한다.
    - `cleanup_tasks`에 대해 음수 인자는 ValueError를 발생시켜 잘못된 입력을 방지한다.

    에지케이스:
    - 타임스탬프나 내부 상태가 예외 발생 후에도 일관성을 유지하는지 추가 검증 가능.
    """
    store = InMemoryTaskStore()
    set_default_store(store)

    # create a task to test type checks
    task_id = run(create_task())

    # passing non-string to get_task should raise TypeError
    with pytest.raises(TypeError):
        run(get_task(123))

    # passing non-string to update_task_status should raise TypeError
    with pytest.raises(TypeError):
        run(update_task_status(123, TaskStatus.failed))

    # cleanup_tasks negative arg raises ValueError
    with pytest.raises(ValueError):
        run(cleanup_tasks(-1))

    reset_default_store()