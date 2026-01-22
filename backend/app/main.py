from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uuid
import shutil
from pathlib import Path
import threading

from app.worker import run_ndvi_job
from app.schemas import NDVIRequest
from app.ee_client import init_ee
from app.tiles import router as tiles_router

# ================================
# CREATE FASTAPI APP
# ================================
app = FastAPI(
    title="Drone-Based Deforestation Monitor",
    version="1.0.0"
)

# ================================
# GLOBAL STORES
# ================================
JOB_STORE: Dict[str, dict] = {}
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ================================
# MIDDLEWARE
# ================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# EARTH ENGINE INIT
# ================================
def init_ee_background():
    try:
        init_ee()
        print("✅ Earth Engine initialized")
    except Exception as e:
        print(f"⚠️ Earth Engine init failed: {e}")

@app.on_event("startup")
def startup():
    threading.Thread(target=init_ee_background, daemon=True).start()

# ================================
# ROUTERS
# ================================
app.include_router(tiles_router)

# ================================
# HEALTH CHECK
# ================================
@app.get("/")
def root():
    return {"status": "ok"}

# ================================
# DRONE IMAGE UPLOAD
# ================================
@app.post("/upload-drone-image")
async def upload_drone_image(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    path = UPLOAD_DIR / f"{file_id}.tif"

    with path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "file_id": file_id,
        "filename": file.filename
    }

# ================================
# ANALYZE ENDPOINT
# ================================
@app.post("/analyze")
async def analyze(
    req: NDVIRequest,
    bg: BackgroundTasks,
    drone_image_id: str | None = None
):
    job_id = str(uuid.uuid4())
    JOB_STORE[job_id] = {"status": "processing"}

    payload = req.dict()

    if drone_image_id:
        payload["drone_image_path"] = str(
            UPLOAD_DIR / f"{drone_image_id}.tif"
        )

    bg.add_task(run_ndvi_job, job_id, payload, JOB_STORE)

    return {"job_id": job_id}

# ================================
# JOB STATUS
# ================================
@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOB_STORE[job_id]
