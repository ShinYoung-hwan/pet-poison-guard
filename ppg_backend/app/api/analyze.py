from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.logger import logger
from app.schemas.task import TaskCreateResponse, TaskStatusResponse, TaskStatus
from app.services.queue_service import run_analysis_task
from app.services.task.task_service import create_task, get_task


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

router = APIRouter(
    prefix='/api'
)

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
async def analyze_image(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    contents = await file.read()
    validate_image_file(file, contents)
    task_id = await create_task({"filename": file.filename, "content_type": file.content_type})
    background_tasks.add_task(run_analysis_task, task_id, (file.filename, contents, file.content_type))
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
async def get_task_status(task_id: str):
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    resp = {"status": task["status"]}
    # TaskStatus enum uses 'completed' for completed state in Phase A
    if task["status"] == TaskStatus.completed:
        resp["data"] = task.get("result")
    elif task["status"] == TaskStatus.failed:
        resp["detail"] = task.get("detail")
    return resp
