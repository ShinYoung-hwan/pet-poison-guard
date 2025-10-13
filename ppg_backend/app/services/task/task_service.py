import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.schemas.task import TaskStatus

# In-memory task store (async-safe)
# TODO : It's not persistent and will lose data on process restart. Replace with Redis/DB for production.
_tasks: Dict[str, Dict[str, Any]] = {}
_lock = asyncio.Lock()

async def create_task(input_meta: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a new in-memory task and return its UUID.

    Args:
        input_meta: Optional metadata about the task input (e.g. file path, filename)

    Returns:
        str: task id (uuid4)
    """
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat() + 'Z'
    async with _lock:
        _tasks[task_id] = {
            "id": task_id,
            "status": TaskStatus.pending,
            "input_meta": input_meta or {},
            "result": None,
            "detail": None,
            "retries": 0,
            "last_error": None,
            "created_at": now,
            "updated_at": now,
        }
    return task_id


async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Return a shallow copy of the task dict or None if not found."""
    async with _lock:
        task = _tasks.get(task_id)
        if task is None:
            return None
        return dict(task)


async def update_task_status(
        task_id: str, 
        status: TaskStatus, 
        *, 
        result: Optional[Any] = None, 
        detail: Optional[str] = None, 
        last_error: Optional[str] = None
        ) -> bool:
    """
    Atomically update task status and optional fields.

    Returns:
        bool: True if task existed and was updated, False otherwise.
    """
    now = datetime.now(timezone.utc).isoformat() + 'Z'
    async with _lock:
        if task_id not in _tasks:
            return False
        t = _tasks[task_id]
        t["status"] = status
        if result is not None:
            t["result"] = result
        if detail is not None:
            t["detail"] = detail
        if last_error is not None:
            t["last_error"] = last_error
        t["updated_at"] = now
    return True


async def save_task_result(task_id: str, result: Any, error: Optional[str] = None) -> bool:
    """
    Save a task's result and mark it done or failed depending on error.
    """
    status = TaskStatus("failed") if error else TaskStatus("completed")
    return await update_task_status(task_id, status, result=result, detail=None, last_error=error)


async def increment_retries(task_id: str) -> int:
    """Increment and return the retries counter for a task. Returns -1 if task not found."""
    async with _lock:
        if task_id not in _tasks:
            return -1
        _tasks[task_id]["retries"] += 1
        _tasks[task_id]["updated_at"] = datetime.now(timezone.utc).isoformat() + 'Z'
        return _tasks[task_id]["retries"]


async def list_tasks() -> Dict[str, Dict[str, Any]]:
    """Return a shallow copy of all tasks (for debugging)."""
    async with _lock:
        return {k: dict(v) for k, v in _tasks.items()}


async def cleanup_tasks(older_than_seconds: int = 24 * 3600) -> int:
    """Remove tasks older than `older_than_seconds`. Returns number removed."""
    cutoff = datetime.now(timezone.utc).timestamp() - older_than_seconds
    removed = 0
    async with _lock:
        keys = list(_tasks.keys())
        for k in keys:
            try:
                t = _tasks[k]
                created_ts = datetime.fromisoformat(t["created_at"].rstrip('Z')).timestamp()
                if created_ts < cutoff:
                    del _tasks[k]
                    removed += 1
            except Exception:
                # If parsing fails, skip
                continue
    return removed
