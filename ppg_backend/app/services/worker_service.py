import asyncio
from typing import List, Optional, Callable, Awaitable, Any

from .queue_service import QueueManager
from .queue_service import get_default_queue_manager, process_task_item
from fastapi.logger import logger

# In-process worker control
_worker_tasks: List[asyncio.Task] = []


async def _worker_loop(
    worker_idx: int,
    shutdown_event: asyncio.Event,
    qm: QueueManager,
    process_fn: Callable[[str, Any], Awaitable[None]],
) -> None:
    """Worker coroutine: consumes from queue until shutdown_event is set and queue is drained.

    This coroutine reads tasks from the provided QueueManager and calls the
    provided async `process_fn(task_id, file_tuple)` for each item.
    """
    logger.info("Worker %d starting", worker_idx)
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

            # item is expected to be (task_id, file_tuple)
            try:
                logger.info("Worker %d processing task %s", worker_idx, item[0])
                task_id, file_tuple = item
                await process_fn(task_id, file_tuple)
            except Exception:
                logger.exception("Error processing task %s in worker %d", item[0], worker_idx)
            finally:
                try:
                    q.task_done()
                except Exception:
                    logger.debug("task_done() failed for worker %d", worker_idx)
    except asyncio.CancelledError:
        logger.info("Worker %d cancelled", worker_idx)
        raise
    finally:
        logger.info("Worker %d stopped", worker_idx)


async def start_workers(
    num_workers: int = 2,
    qm: Optional[QueueManager] = None,
    process_fn: Optional[Callable[[str, Any], Awaitable[None]]] = None,
) -> asyncio.Event:
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


async def stop_workers(
    shutdown_event: asyncio.Event,
    qm: Optional[QueueManager] = None,
    timeout: float = 5.0,
) -> None:
    """Signal workers to stop and wait for them to finish.

    This will set the shutdown_event and wait for worker tasks to finish. If the
    queue does not drain within `timeout`, remaining worker tasks are cancelled.
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