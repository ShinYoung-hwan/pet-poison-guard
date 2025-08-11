from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid

from enum import Enum

app = FastAPI()

class JobStatus(str, Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"

# 임시로 작업 상태와 결과를 저장할 딕셔너리 (실제로는 Redis, DB 등 사용)
jobs = {}

class JobResponse(BaseModel):
    job_id: str

class ResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: dict | None = None
    detail: str | None = None

# --- AI Worker Function (실제로는 Celery 등 Task Queue에서 실행) ---
def run_ai_analysis(job_id: str, image_bytes: bytes):
    """ AI 모델을 실행하는 가상 함수 """
    
    import time
    print(f"Job {job_id}: AI 분석 시작...")
    
    try:
        time.sleep(10) # AI 연산을 10초 슬립으로 가정
    except Exception as e:
        jobs[job_id]['status'] = JobStatus.failed
        jobs[job_id]['detail'] = str(e)
        return

    # 분석 결과 생성
    analysis_result = {
        "description": f"Image analysis for {job_id} complete.",
        "confidence": 0.95
    }
    jobs[job_id]['status'] = JobStatus.completed
    jobs[job_id]['result'] = analysis_result
    print(f"Job {job_id}: AI 분석 완료.")


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Image Analysis API"}

@app.post("/api/v1/analysis", response_model=JobResponse, status_code=202)
async def request_analysis(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """이미지를 받아 AI 분석 작업을 시작시키는 엔드포인트"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")

    job_id = str(uuid.uuid4())
    image_bytes = await file.read()
    
    # 작업을 딕셔너리에 저장하고 상태를 'processing'으로 설정
    jobs[job_id] = {
            "status": JobStatus.processing,
            "result": None
        }

    # 백그라운드에서 AI 작업 실행
    background_tasks.add_task(run_ai_analysis, job_id, image_bytes)
    
    return {
            "job_id": job_id
        }


@app.get("/api/v1/analysis/{job_id}", response_model=ResultResponse)
async def get_analysis_result(job_id: str):
    """Job ID를 사용하여 분석 상태 및 결과를 조회하는 엔드포인트"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="요청하신 작업을 찾을 수 없습니다.")

    try:
        return ResultResponse(job_id=job_id, status=job['status'], result=job.get('result'))
    finally:
        # 작업이 완료되면 딕셔너리에서 제거 (실제 환경에서는 DB나 캐시에서 삭제)
        if job['status'] == JobStatus.completed:
            del jobs[job_id]