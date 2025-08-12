from fastapi import APIRouter

router = APIRouter()

@router.get("/health", summary="Health check", status_code=200)
async def health():
    """Returns service health status."""
    return {"status": "ok"}
