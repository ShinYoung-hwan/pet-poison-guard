from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.logger import logger
from app.schemas.task import TaskCreateResponse, TaskStatusResponse, TaskStatus
from app.services.ai_service import request_ai_analysis
from app.services.task_service import create_task, set_task_completed, set_task_failed, get_task

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

router = APIRouter(
    prefix='/api'
)

def validate_image_file(file: UploadFile, contents: bytes):
    if not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(status_code=400, detail="Only image files are allowed.")
    if len(contents) > MAX_FILE_SIZE:
        logger.warning(f"File too large: {len(contents)} bytes")
        raise HTTPException(status_code=413, detail="File too large. Max 5MB allowed.")

async def run_analysis_task(task_id: str, file_tuple):
    try:
        ai_result = await request_ai_analysis(file_tuple)
        set_task_completed(task_id, ai_result)
        logger.info(f"AI analysis complete for {task_id}")
    except Exception as e:
        set_task_failed(task_id, str(e))
        logger.error(f"AI analyze error for {task_id}: {str(e)}")

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
    task_id = create_task()
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
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    resp = {"status": task["status"]}
    if task["status"] == TaskStatus.completed:
        resp["data"] = task["data"]
    elif task["status"] == TaskStatus.failed:
        resp["detail"] = task["detail"]
    return resp
