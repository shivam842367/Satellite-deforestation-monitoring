from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uuid
import shutil
from pathlib import Path

from app.worker import run_ndvi_job
from app.schemas import NDVIRequest
from app.ee_client import init_ee

JOB_STORE: Dict[str, dict] = {}
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Deforestation Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_ee()


@app.post("/upload-drone-image")
async def upload(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    path = UPLOAD_DIR / f"{file_id}.tif"

    with path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"file_id": file_id}


@app.post("/analyze")
async def analyze(req: NDVIRequest, bg: BackgroundTasks, drone_image_id: str = None):

    job_id = str(uuid.uuid4())
    JOB_STORE[job_id] = {"status": "processing"}

    payload = req.dict()

    if drone_image_id:
        payload["drone_image_path"] = str(UPLOAD_DIR / f"{drone_image_id}.tif")

    bg.add_task(run_ndvi_job, job_id, payload, JOB_STORE)

    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def job(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(404, "Job not found")
    return JOB_STORE[job_id]
