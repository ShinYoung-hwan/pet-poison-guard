import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.logger import logger
from app.schemas.analyze import AnalyzeResponse, AnalyzeResult
from app.services.ai_service import request_ai_analysis

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

router = APIRouter()

def validate_image_file(file: UploadFile, contents: bytes):
    if not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(status_code=400, detail="Only image files are allowed.")
    if len(contents) > MAX_FILE_SIZE:
        logger.warning(f"File too large: {len(contents)} bytes")
        raise HTTPException(status_code=413, detail="File too large. Max 5MB allowed.")

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze food image",
    status_code=200,
    responses={
        200: {"description": "Analysis result returned."},
        400: {"description": "Invalid file type."},
        413: {"description": "File too large."},
        502: {"description": "AI server error."},
        504: {"description": "AI server timeout."},
        500: {"description": "Internal server error."}
    }
)
async def analyze_image(file: UploadFile = File(...)):
    contents = await file.read()
    validate_image_file(file, contents)
    try:
        ai_result = await request_ai_analysis((file.filename, contents, file.content_type))
        logger.info(f"AI server response: {ai_result}")
        return {"result": AnalyzeResult(**ai_result)}
    except Exception as e:
        logger.error(f"AI analyze error: {str(e)}")
        if hasattr(e, 'status_code') and e.status_code == 504:
            raise HTTPException(status_code=504, detail="AI server timeout. Please try again later.")
        elif hasattr(e, 'status_code') and e.status_code == 502:
            raise HTTPException(status_code=502, detail="AI server error.")
        raise HTTPException(status_code=500, detail="Internal server error.")
