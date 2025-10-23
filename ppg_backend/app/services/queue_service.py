from typing import Tuple, List, Dict, Optional, Callable, Any
import asyncio
import os
from fastapi.logger import logger

from .ai_service import image_to_embedding
from .db_service import find_poisons_in_recipe, find_top_k_recipes
from app.models.db_session import AsyncSessionLocal
from app.services.task.task_service import (
    save_task_result,
    update_task_status,
    increment_retries,
)
from app.schemas.task import TaskStatus


class QueueManager:
    """Lightweight in-process queue manager with injectable processing callback.

    This class encapsulates queue creation and exposes enqueue/get operations. Tests
    can instantiate their own QueueManager and pass a custom process callback to workers.
    """

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()

    def ensure(self) -> asyncio.Queue:
        return self._queue

    async def enqueue(self, task_id: str, file_tuple: Tuple[str, str, str]) -> None:
        """Put a task into the in-memory queue.

        Args:
            task_id: Task identifier.
            file_tuple: Expected (tmp_path, filename, content_type).
        """
        await self._queue.put((task_id, file_tuple))

    async def get(self) -> Tuple[str, str, str]:
        return await self._queue.get()


_default_queue_manager: Optional[QueueManager] = None


def get_default_queue_manager() -> QueueManager:
    global _default_queue_manager
    if _default_queue_manager is None:
        _default_queue_manager = QueueManager()
    return _default_queue_manager


async def process_task_item(
    task_id: str,
    file_tuple: Tuple[str, str, str],
    *,
    request_ai_fn: Optional[Callable[..., Any]] = None,
    save_fn: Optional[Callable[..., Any]] = None,
    update_status_fn: Optional[Callable[..., Any]] = None,
) -> None:
    """Process one queued task.

    Args:
        task_id: Task identifier.
        file_tuple: Expected tuple (tmp_path, filename, content_type).
        request_ai_fn: Optional override for AI request function.
        save_fn: Optional override for result save function.
        update_status_fn: Optional override for status update function.
    """
    tmp_path: Optional[str] = None
    request_ai_fn = request_ai_fn or request_ai_analysis
    save_fn = save_fn or save_task_result
    update_status_fn = update_status_fn or update_task_status
    try:
        tmp_path, filename, content_type = file_tuple
        ai_result = await request_ai_fn(tmp_path, timeout=15.0, top_k=10)
        await save_fn(task_id, ai_result)
        logger.info("AI analysis complete for %s", task_id)
    except Exception as e:  # capture any runtime error and persist status
        err_str = str(e)
        try:
            await update_status_fn(task_id, TaskStatus.failed, last_error=err_str)
            await increment_retries(task_id)
        except Exception:
            logger.exception("Failed to update task status for %s", task_id)
        logger.error("AI analyze error for %s: %s", task_id, err_str)
    finally:
        # ensure temporary file is removed if it exists
        if tmp_path:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                logger.warning("Failed to remove temp file %s", tmp_path)


async def run_analysis_task(task_id: str, file_tuple: Tuple[str, str, str]):
    """Compatibility wrapper: process immediately (used by BackgroundTasks or tests).

    Prefer using `enqueue(task_id, file_tuple)` so work is handled by worker pool.
    """
    await process_task_item(task_id, file_tuple)


# Global semaphore for request_ai_analysis
_request_ai_analysis_semaphore: Optional[asyncio.Semaphore] = None

async def request_ai_analysis(
    tmp_path: str,
    timeout: float = 15.0,
    top_k: int = 10,
) -> List[Dict[str, str]]:
    """Run the AI analysis pipeline for a single image file.

    The function serializes calls to the computation-bound embedding extraction using a
    module-level semaphore to avoid contention.
    """
    # Semaphore ensures image_to_embedding is run serially to avoid heavy CPU contention
    # TODO: Verify that using a global semaphore and run_in_executor for image_to_embedding
    # is appropriate when model inference runs on GPU. Things to check and consider:
    # - Ensure proper concurrency control given GPU memory limits and model thread-safety.
    # - Make the semaphore's concurrency limit configurable (e.g. via env var) rather than hard-coded.
    # - Evaluate whether a process-based executor or a dedicated model worker/process (or model server)
    #   is preferable for GPU inference to avoid multithreaded CUDA issues.
    # - Confirm the model is loaded on the intended device and use torch.inference_mode()/no_grad()
    #   and proper device/context management during inference.
    # - If continuing to use run_in_executor, test PyTorch/CUDA behavior in multithreaded contexts
    #   and switch to multiprocessing or an external inference service if necessary.
    global _request_ai_analysis_semaphore
    if _request_ai_analysis_semaphore is None:
        _request_ai_analysis_semaphore = asyncio.Semaphore(1)

    async with _request_ai_analysis_semaphore:
        # image_to_embedding is blocking; run in executor to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        query_emb = await loop.run_in_executor(None, image_to_embedding, tmp_path)

    # Query DB for top-k recipes and find poisons
    async with AsyncSessionLocal() as db:
        topk = await find_top_k_recipes(db, query_emb, top_k=top_k)
        poisons = await find_poisons_in_recipe(db, topk)
        return poisons


def ensure_queue_manager() -> QueueManager:
    return get_default_queue_manager()


async def enqueue(task_id: str, file_tuple: Tuple) -> None:
    """Put a task into the default in-process queue for workers to pick up."""
    qm = ensure_queue_manager()
    await qm.enqueue(task_id, file_tuple)
