import uuid
from enum import Enum
from typing import Dict, Any, Union
from app.schemas.task import TaskStatus

# In-memory task store (for demo)
# TODO: use Redis/DB in production
# TODO: add expiration and cleanup
tasks: Dict[str, Dict[str, Any]] = {}

def create_task() -> str:
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": TaskStatus.pending, "data": None, "detail": None}
    return task_id

def set_task_completed(task_id: str, data: Any):
    if task_id in tasks:
        tasks[task_id]["status"] = TaskStatus.completed
        tasks[task_id]["data"] = data

def set_task_failed(task_id: str, detail: str):
    if task_id in tasks:
        tasks[task_id]["status"] = TaskStatus.failed
        tasks[task_id]["detail"] = detail

def get_task(task_id: str) -> Union[Dict[str, Any], None]:
    return tasks.get(task_id, None)
