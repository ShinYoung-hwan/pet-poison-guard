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