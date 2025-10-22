import asyncio
from typing import List, Optional, Callable

from .queue_service import QueueManager
from .queue_service import get_default_queue_manager, process_task_item
from fastapi.logger import logger

# In-process worker control
_worker_tasks: List[asyncio.Task] = []


async def _worker_loop(worker_idx: int, shutdown_event: asyncio.Event, qm: QueueManager, process_fn: Callable):
    """Worker coroutine: consumes from queue until shutdown_event is set and queue is drained."""
    logger.info(f"Worker {worker_idx} starting")
    q = qm.ensure()
    try:
        while True:
            try:
                item = await asyncio.wait_for(q.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # check for shutdown
                if shutdown_event.is_set() and q.empty():
                    break
                continue
            logger.info(f"Worker {worker_idx} processing task {item[0]}")
            task_id, file_tuple = item
            try:
                await process_fn(task_id, file_tuple)
            finally:
                q.task_done()
    except asyncio.CancelledError:
        logger.info(f"Worker {worker_idx} cancelled")
        raise
    finally:
        logger.info(f"Worker {worker_idx} stopped")


async def start_workers(num_workers: int = 2, qm=None, process_fn: Optional[Callable] = None) -> asyncio.Event:
    """Start worker coroutines and return a shutdown event used to stop them later.

    Caller may provide a custom QueueManager and process_fn for testing.
    """
    global _worker_tasks
    shutdown_event = asyncio.Event()
    qm = qm or get_default_queue_manager()
    process_fn = process_fn or (lambda tid, ft: process_task_item(tid, ft))
    # Launch workers
    for i in range(num_workers):
        t = asyncio.create_task(_worker_loop(i, shutdown_event, qm, process_fn))
        _worker_tasks.append(t)
    return shutdown_event


async def stop_workers(shutdown_event: asyncio.Event, qm: Optional[QueueManager] = None, timeout: float = 5.0) -> None:
    """Signal workers to stop and wait for them to finish.

    This will set the shutdown_event and wait for worker tasks to finish.
    """
    global _worker_tasks
    qm = qm or get_default_queue_manager()
    shutdown_event.set()
    # Wait for queue to be drained
    q = qm.ensure()
    try:
        await asyncio.wait_for(q.join(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for queue to drain during shutdown")
    # Cancel any remaining tasks
    for t in _worker_tasks:
        if not t.done():
            t.cancel()
    # Await cancellation
    await asyncio.gather(*_worker_tasks, return_exceptions=True)
    _worker_tasks = []