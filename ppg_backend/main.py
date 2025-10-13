import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.logger import logger
from app.api import analyze, health
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)

# --- Startup event ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.ai_service import load_model
    from app.services.worker_service import start_workers, stop_workers
    # Load global resources
    load_model()
    # Start in-process worker pool
    shutdown_event = await start_workers()
    app.state._task_queue_shutdown = shutdown_event
    yield
    # Cleanup workers
    try:
        await stop_workers(app.state._task_queue_shutdown)
    except Exception:
        logger.exception("Error during worker shutdown")

app = FastAPI(
    title="Pet Poison Guard Backend API",
    description="REST API for pet food safety image analysis.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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