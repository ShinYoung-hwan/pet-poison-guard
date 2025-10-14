from typing import Any, Dict, Optional
from . import task_service

# -------------------------
# Task helper wrappers (Phase A - in-memory)
# These functions provide a small task-management API for the rest of the
# application. During Phase A tasks are stored in-process (see task_service).
# They are async and non-blocking; callers should await them.
# Replace these wrappers with DB-backed implementations when migrating.


async def create_task(input_meta: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a new task in the in-memory task store and return its id.

    This is an async wrapper around `task_service.create_task`. It is
    non-blocking and safe to call from async FastAPI endpoints or workers.
    """
    return await task_service.create_task(input_meta)


async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Return task info dict or None if not found."""
    return await task_service.get_task(task_id)


async def update_task_status(task_id: str, status: str, *, result: Optional[Any] = None, detail: Optional[str] = None, last_error: Optional[str] = None) -> bool:
    """
    Update the task status and optional fields. `status` should be one of the
    values defined in `app.schemas.task.TaskStatus`.
    """
    # Delegate to task_service which handles locking/consistency
    from app.schemas.task import TaskStatus as _TS
    try:
        _status = _TS(status)
    except Exception:
        # invalid status
        return False
    return await task_service.update_task_status(task_id, _status, result=result, detail=detail, last_error=last_error)


async def save_task_result(task_id: str, result: Any, error: Optional[str] = None) -> bool:
    """
    Persist the task result in the current in-memory store. If `error` is set
    the task will be marked failed; otherwise marked done.
    """
    return await task_service.save_task_result(task_id, result, error=error)
