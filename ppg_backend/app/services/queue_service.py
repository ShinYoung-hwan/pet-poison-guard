from typing import Tuple, List, Dict, Optional
import asyncio
import os
import tempfile
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

# Concurrency primitives
_semaphore = asyncio.Semaphore(1)
# In-process queue 
_task_queue: Optional[asyncio.Queue] = None


async def process_task_item(task_id: str, file_tuple: Tuple):
    """Process one queued task (file_tuple is expected to be (tmp_path, filename, content_type))."""
    tmp_path = None
    try:
        tmp_path, filename, content_type = file_tuple
        ai_result = await request_ai_analysis(tmp_path, timeout=15.0, top_k=10)
        await save_task_result(task_id, ai_result)
        logger.info(f"AI analysis complete for {task_id}")
    except Exception as e:
        # mark failed and save error
        await update_task_status(task_id, TaskStatus.failed, last_error=str(e))
        logger.error(f"AI analyze error for {task_id}: {str(e)}")
    finally:
        # ensure temporary file is removed if it exists
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            logger.warning(f"Failed to remove temp file {tmp_path}")


async def run_analysis_task(task_id: str, file_tuple):
    """Compatibility wrapper: process immediately (used by BackgroundTasks or tests).

    Prefer using `enqueue(task_id, file_tuple)` so work is handled by worker pool.
    """
    await process_task_item(task_id, file_tuple)


async def request_ai_analysis(tmp_path: str, timeout: float = 15.0, top_k: int = 10) -> List[Dict[str, str]]:
    """
    tmp_path: path to the image file on disk
    Returns: list of dicts [{"name": ..., "image": ..., "description": ...}], sorted by similarity descending
    """
    async with _semaphore:
        # image_to_embedding is blocking; run in executor to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        query_emb = await loop.run_in_executor(None, image_to_embedding, tmp_path)

    # Query DB for top-k recipes and find poisons
    async with AsyncSessionLocal() as db:
        try:
            topk = await find_top_k_recipes(db, query_emb, top_k=top_k)
            poisons = await find_poisons_in_recipe(db, topk)
            return poisons
        finally:
            pass


def ensure_queue():
    """Ensure the global in-process task queue is initialized."""
    global _task_queue
    if _task_queue is None:
        _task_queue = asyncio.Queue()
    return _task_queue


async def enqueue(task_id: str, file_tuple: Tuple) -> None:
    """Put a task into the in-process queue for workers to pick up."""
    # TODO : enqueue bytes to disk-backed queue if too large 
    q = ensure_queue()
    await q.put((task_id, file_tuple))
