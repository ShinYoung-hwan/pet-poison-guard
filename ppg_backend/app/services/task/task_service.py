"""Task service - in-memory task store and module-level wrappers.

This module provides an async-safe in-memory task store implementation
(`InMemoryTaskStore`) and a set of module-level async wrapper functions
maintained for backwards compatibility with existing callers.

Design goals:
- Simple async-safe in-memory implementation for tests and local runs.
- Clear, typed public API and docstrings describing inputs/outputs/exceptions.
- Ability to replace the default store with `set_default_store()` in tests.

Note: This store is not persistent and will lose data on process restart.
For production, replace with a DB or Redis-backed implementation that
implements the same async interface.
"""

import asyncio
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from app.schemas.task import TaskStatus


class InMemoryTaskStore:
    """An async-safe in-memory task store implementing the expected task service interface.

    Methods are asynchronous to match existing code and allow easy swapping with other async stores.
    """

    def __init__(self) -> None:
        """Create a fresh in-memory store.

        The store is protected by an asyncio.Lock to allow safe concurrent access
        from async worker coroutines.
        """
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create_task(self, input_meta: Optional[Dict[str, Any]] = None) -> str:
        """Create a new task record and return its id.

        Args:
            input_meta: Optional metadata about the task input (e.g. file path, filename).

        Returns:
            A UUID4 string representing the created task id.

        Examples:
            >>> await store.create_task({"filename": "a.png"})
            'b7a9f2f0-...'
        """
        task_id = str(uuid.uuid4())
        # Store a single numeric epoch timestamp (seconds, float) as the
        # canonical value for created_at/updated_at. This avoids fragile
        # string parsing for internal comparisons. For backward
        # compatibility we still accept legacy ISO strings on read.
        now_ts = time.time()
        async with self._lock:
            self._tasks[task_id] = {
                "id": task_id,
                "status": TaskStatus.pending,
                "input_meta": input_meta or {},
                "result": None,
                "detail": None,
                "retries": 0,
                "last_error": None,
                # canonical numeric timestamps
                "created_at": now_ts,
                "updated_at": now_ts,
            }
        return task_id

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Return a shallow copy of the task dict or None if not found.

        Args:
            task_id: Task identifier string.

        Returns:
            A shallow copy of the stored task dict, or None when the id does not exist.
        """
        if not isinstance(task_id, str):
            raise TypeError("task_id must be a string")
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            return dict(task)

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        *,
        result: Optional[Any] = None,
        detail: Optional[str] = None,
        last_error: Optional[str] = None,
    ) -> bool:
        """Atomically update task status and optional fields.

        Args:
            task_id: The task identifier to update.
            status: A `TaskStatus` enum value.
            result: Optional result payload to store.
            detail: Optional human-readable detail.
            last_error: Optional error message string.

        Returns:
            True if the task existed and was updated; False otherwise.

        Raises:
            TypeError: if task_id is not a string.
        """
        if not isinstance(task_id, str):
            raise TypeError("task_id must be a string")
        # Update the canonical numeric timestamp
        now_ts = time.time()
        async with self._lock:
            if task_id not in self._tasks:
                return False
            t = self._tasks[task_id]
            t["status"] = status
            if result is not None:
                t["result"] = result
            if detail is not None:
                t["detail"] = detail
            if last_error is not None:
                t["last_error"] = last_error
            t["updated_at"] = now_ts
        return True

    async def save_task_result(self, task_id: str, result: Any, error: Optional[str] = None) -> bool:
        """Save a task's result and mark it done or failed depending on error.

        Args:
            task_id: Task identifier string.
            result: The analysis result payload to store.
            error: Optional error string; when provided, the task will be marked failed.

        Returns:
            True if the update succeeded, False otherwise.
        """
        status = TaskStatus.failed if error else TaskStatus.completed
        return await self.update_task_status(task_id, status, result=result, detail=None, last_error=error)

    async def increment_retries(self, task_id: str) -> int:
        """Increment and return the retries counter for a task.

        Returns -1 if the task_id was not found.
        """
        if not isinstance(task_id, str):
            raise TypeError("task_id must be a string")
        async with self._lock:
            if task_id not in self._tasks:
                return -1
            self._tasks[task_id]["retries"] += 1
            now_ts = time.time()
            self._tasks[task_id]["updated_at"] = now_ts
            return self._tasks[task_id]["retries"]

    async def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Return a shallow copy of all tasks (for debugging).

        Returns a mapping of task_id to task dicts.
        """
        async with self._lock:
            return {k: dict(v) for k, v in self._tasks.items()}

    async def cleanup_tasks(self, older_than_seconds: int = 24 * 3600) -> int:
        """Remove tasks older than `older_than_seconds`.

        Args:
            older_than_seconds: Age threshold in seconds; tasks older than this value
                will be removed.

        Returns:
            Number of tasks removed.
        """
        if not isinstance(older_than_seconds, (int, float)) or older_than_seconds < 0:
            raise ValueError("older_than_seconds must be a non-negative number")
        # Use epoch seconds for cutoff; prefer numeric stored timestamps,
        # but fall back to parsing legacy ISO strings if necessary.
        cutoff = time.time() - older_than_seconds
        removed = 0
        async with self._lock:
            keys = list(self._tasks.keys())
            for k in keys:
                try:
                    t = self._tasks[k]
                    # Prefer numeric created_at (new canonical form). If it's a
                    # string (legacy), attempt to parse; otherwise skip if
                    # unknown.
                    created_ts = t.get("created_at")
                    if isinstance(created_ts, str):
                        try:
                            created_ts = datetime.fromisoformat(created_ts.rstrip('Z')).timestamp()
                        except Exception:
                            continue
                    if created_ts is None:
                        # No usable created_at; skip
                        continue
                    if created_ts < cutoff:
                        del self._tasks[k]
                        removed += 1
                except Exception:
                    continue
        return removed


# Default store instance used by module-level wrapper functions.
_default_store: InMemoryTaskStore = InMemoryTaskStore()


def set_default_store(store: InMemoryTaskStore) -> None:
    """Replace the module-level default task store (useful for tests).

    Args:
        store: An instance implementing the InMemoryTaskStore async interface.

    Raises:
        TypeError: if `store` does not provide required coroutine attributes.
    """
    if not hasattr(store, "create_task") or not asyncio.iscoroutinefunction(store.create_task):
        raise TypeError("store must implement async create_task method")
    global _default_store
    _default_store = store


def reset_default_store() -> None:
    """Reset the module-level default store to a fresh in-memory store."""
    global _default_store
    _default_store = InMemoryTaskStore()


# Module-level async wrappers (backwards-compatible API)
async def create_task(input_meta: Optional[Dict[str, Any]] = None) -> str:
    return await _default_store.create_task(input_meta)


async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    return await _default_store.get_task(task_id)


async def update_task_status(
    task_id: str,
    status: TaskStatus,
    *,
    result: Optional[Any] = None,
    detail: Optional[str] = None,
    last_error: Optional[str] = None,
) -> bool:
    return await _default_store.update_task_status(task_id, status, result=result, detail=detail, last_error=last_error)


async def save_task_result(task_id: str, result: Any, error: Optional[str] = None) -> bool:
    return await _default_store.save_task_result(task_id, result, error)


async def increment_retries(task_id: str) -> int:
    return await _default_store.increment_retries(task_id)


async def list_tasks() -> Dict[str, Dict[str, Any]]:
    return await _default_store.list_tasks()


async def cleanup_tasks(older_than_seconds: int = 24 * 3600) -> int:
    return await _default_store.cleanup_tasks(older_than_seconds)
