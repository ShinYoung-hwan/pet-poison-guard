from typing import Tuple, List, Dict
import asyncio
import os
import tempfile
from fastapi.logger import logger

from .ai_service import image_to_embedding
from .db_service import find_poisons_in_recipe, find_top_k_recipes
from app.models.db_session import AsyncSessionLocal
from app.services.task.task_service import save_task_result, update_task_status, increment_retries
from app.schemas.task import TaskStatus

semaphore = asyncio.Semaphore(1)

async def run_analysis_task(task_id: str, file_tuple):
    try:
        ai_result = await request_ai_analysis(file_tuple)
        await save_task_result(task_id, ai_result)
        logger.info(f"AI analysis complete for {task_id}")
    except Exception as e:
        await update_task_status(task_id, TaskStatus.failed, last_error=str(e))
        logger.error(f"AI analyze error for {task_id}: {str(e)}")

async def request_ai_analysis(file: Tuple, timeout: float = 15.0, top_k: int = 10) -> List[Dict[str, str]]:
    """
    file: tuple (filename, fileobj, content_type)
    Returns: list of dicts [{"name": ..., "image": ..., "description": ...}], sorted by similarity descending
    """
    async with semaphore:
        filename, fileobj, content_type = file
        with tempfile.NamedTemporaryFile(delete=True, suffix=os.path.splitext(filename)[-1]) as tmp:
            tmp.write(fileobj)
            tmp.flush()
            # image_to_embedding is blocking; run in executor to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            query_emb = await loop.run_in_executor(None, image_to_embedding, tmp.name)
    
    # instead of using get_db()
    async with AsyncSessionLocal() as db:
        try:
            topk = await find_top_k_recipes(db, query_emb, top_k=top_k)
            poisons = await find_poisons_in_recipe(db, topk)
            return poisons
        finally:
            # async with will close the session; nothing to do here
            pass