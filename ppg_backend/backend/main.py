
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.logger import logger
from app.api import analyze, health

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Pet Poison Guard Backend API",
    description="REST API for pet food safety image analysis.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Register Routers ---
app.include_router(analyze.router)
app.include_router(health.router)

# --- Error handler for generic error hiding sensitive info ---
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."}
    )