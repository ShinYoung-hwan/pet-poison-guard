from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
import tempfile
import os
from fastapi.logger import logger
from typing import Callable, Any, Optional
from app.schemas.task import TaskCreateResponse, TaskStatusResponse, TaskStatus
from app.services.utils import get_max_file_size
from app.services.exceptions import AIServiceError, DBServiceError


MAX_FILE_SIZE = get_max_file_size()

router = APIRouter(
    prefix='/api'
)


def get_create_task_fn() -> Callable[..., Any]:
    """FastAPI dependency returning the create_task callable.

    Tests can override this dependency via app.dependency_overrides.
    The returned callable is expected to be: async def create_task(input_meta: dict) -> str
    """
    from app.services.task.task_service import create_task
    return create_task


def get_enqueue_fn() -> Callable[..., Any]:
    from app.services.queue_service import enqueue
    return enqueue


def get_run_task_fn() -> Callable[..., Any]:
    from app.services.queue_service import run_analysis_task
    return run_analysis_task


def get_task_fn() -> Callable[..., Any]:
    from app.services.task.task_service import get_task
    return get_task


def validate_image_file(file: UploadFile, contents: bytes) -> None:
    """Validate uploaded file is an image and under the size limit.

    Raises HTTPException on invalid input.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning("Invalid file type: %s", file.content_type)
        raise HTTPException(status_code=400, detail="Only image files are allowed.")
    if len(contents) > MAX_FILE_SIZE:
        logger.warning("File too large: %d bytes", len(contents))
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
    create_task_fn: Callable[..., Any] = Depends(get_create_task_fn),
    enqueue_fn: Callable[..., Any] = Depends(get_enqueue_fn),
    run_task_fn: Callable[..., Any] = Depends(get_run_task_fn),
) -> TaskCreateResponse:
    """Accept an image upload, create a task id and schedule analysis.

    The uploaded bytes are written to a temporary file path which is passed to
    the queue/workers to avoid keeping large blobs in memory.
    """
    contents = await file.read()
    validate_image_file(file, contents)
    task_id = await create_task_fn({"filename": file.filename, "content_type": file.content_type})

    tmp_path: Optional[str] = None
    suffix = os.path.splitext(file.filename)[-1] if file.filename else None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp.flush()
            tmp_path = tmp.name

        # enqueue a small tuple (tmp_path, original filename, content_type)
        try:
            await enqueue_fn(task_id, (tmp_path, file.filename, file.content_type))
        except (AIServiceError, DBServiceError) as e:
            logger.warning("Enqueue failed due to domain error, falling back to background task: %s", str(e))
            background_tasks.add_task(run_task_fn, task_id, (tmp_path, file.filename, file.content_type))
        except Exception as e:
            logger.exception("Unexpected error while enqueueing task %s : %s", task_id, str(e))
            # Fallback to background task execution; the background task will
            # be responsible for cleaning up the temp file when done.
            background_tasks.add_task(run_task_fn, task_id, (tmp_path, file.filename, file.content_type))
    except Exception as e:
        logger.exception("Unexpected error while processing file %s : %s", file.filename, str(e))
        # cleanup on failure
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning("Failed to remove temp file during error cleanup: %s : %s", tmp_path, str(e))
        raise

    return TaskCreateResponse(taskId=task_id)


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
        get_task_fn: Callable[..., Any] = Depends(get_task_fn)
    ) -> TaskStatusResponse:
    """Get task status using an injectable get_task function (overridable in tests).

    The default dependency imports `get_task` from `app.services.task.task_service`.
    """
    task = await get_task_fn(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    # Coerce stored status to TaskStatus enum if needed
    stored_status = task.get("status")
    try:
        status_enum = TaskStatus(stored_status) if not isinstance(stored_status, TaskStatus) else stored_status
    except Exception:
        # Unknown status stored; return as-is as a string in the detail
        return TaskStatusResponse(status=TaskStatus.pending, detail=f"unknown status: {stored_status}")

    resp = TaskStatusResponse(status=status_enum)
    if status_enum == TaskStatus.completed:
        resp.data = task.get("result")
    elif status_enum == TaskStatus.failed:
        resp.detail = task.get("detail")
    return resp
