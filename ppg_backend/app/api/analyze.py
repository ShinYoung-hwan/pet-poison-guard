from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
import tempfile
import os
from fastapi.logger import logger
from typing import Callable
from app.schemas.task import TaskCreateResponse, TaskStatusResponse, TaskStatus
from app.services.utils import get_max_file_size
from app.services.exceptions import AIServiceError, DBServiceError


MAX_FILE_SIZE = get_max_file_size()

router = APIRouter(
    prefix='/api'
)


def get_create_task_fn() -> Callable:
    """FastAPI dependency returning the create_task callable.

    Tests can override this dependency via app.dependency_overrides.
    """
    from app.services.task.task_service import create_task
    return create_task


def get_enqueue_fn() -> Callable:
    from app.services.queue_service import enqueue
    return enqueue


def get_run_task_fn() -> Callable:
    from app.services.queue_service import run_analysis_task
    return run_analysis_task


def get_task_fn() -> Callable:
    from app.services.task.task_service import get_task
    return get_task

def validate_image_file(file: UploadFile, contents: bytes):
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(status_code=400, detail="Only image files are allowed.")
    if len(contents) > MAX_FILE_SIZE:
        logger.warning(f"File too large: {len(contents)} bytes")
        raise HTTPException(status_code=413, detail="File too large. Max 5MB allowed.")

@router.post(
    "/analyze",
    response_model=TaskCreateResponse,
    summary="Analyze food image (async)",
    status_code=202,
    responses={
        202: {"description": "Task created."},
        400: {"description": "Invalid file type."},
        413: {"description": "File too large."},
        500: {"description": "Internal server error."}
    }
)
async def analyze_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    create_task_fn: Callable = Depends(get_create_task_fn),
    enqueue_fn: Callable = Depends(get_enqueue_fn),
    run_task_fn: Callable = Depends(get_run_task_fn),
):
    contents = await file.read()
    validate_image_file(file, contents)
    task_id = await create_task_fn({"filename": file.filename, "content_type": file.content_type})
    # Prefer enqueueing to the worker pool. enqueue is async and will schedule the work
    # quickly; callers still get an immediate 202 with task id.
    # Persist uploaded bytes to a temp file and enqueue the temp path (to avoid keeping bytes in memory)
    tmp_path = None
    try:
        suffix = os.path.splitext(file.filename)[-1] if file.filename else None
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp.flush()
            tmp_path = tmp.name
        # enqueue a small tuple (tmp_path, original filename, content_type)
        try:
            await enqueue_fn(task_id, (tmp_path, file.filename, file.content_type))
        except (AIServiceError, DBServiceError):
            # Domain errors: fallback to background execution
            background_tasks.add_task(run_task_fn, task_id, (tmp_path, file.filename, file.content_type))
        except Exception:
            # Generic fallback: schedule direct background task if enqueue fails
            background_tasks.add_task(run_task_fn, task_id, (tmp_path, file.filename, file.content_type))
    except Exception:
        # cleanup on failure
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise
    return {"taskId": task_id}

@router.get(
    "/task/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get analysis task status/result",
    responses={
        200: {"description": "Task status/result returned."},
        404: {"description": "Task not found."}
    }
)
async def get_task_status(
        task_id: str, 
        get_task_fn: Callable = Depends(get_task_fn)
    ):
    """Get task status using an injectable get_task function (overridable in tests).

    The default dependency imports `get_task` from `app.services.task.task_service`.
    """
    task = await get_task_fn(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    resp = {"status": task["status"]}
    # TaskStatus enum uses 'completed' for completed state in Phase A
    if task["status"] == TaskStatus.completed:
        resp["data"] = task.get("result")
    elif task["status"] == TaskStatus.failed:
        resp["detail"] = task.get("detail")
    return resp
