from pydantic import BaseModel, Field
from typing import Optional

class AnalyzeResult(BaseModel):
    is_safe: bool = Field(..., description="Is the food safe for pets?")
    label: str = Field(..., description="Detected food label")
    confidence: float = Field(..., description="Model confidence (0~1)")
    message: str = Field(..., description="Analysis summary message")

class AnalyzeCreateResponse(BaseModel):
    taskId: str

class AnalyzeResponse(BaseModel):
    result: Optional[AnalyzeResult]
