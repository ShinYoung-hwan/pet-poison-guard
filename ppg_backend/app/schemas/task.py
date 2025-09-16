from pydantic import BaseModel
from enum import Enum
from typing import Any, Optional

class TaskStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class TaskCreateResponse(BaseModel):
    taskId: str

class TaskStatusResponse(BaseModel):
    status: TaskStatus
    data: Optional[Any] = None
    detail: Optional[str] = None
