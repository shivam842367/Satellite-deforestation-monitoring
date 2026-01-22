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

from app.routes.analyze import router as analyze_router
from app.routes.jobs import router as jobs_router
from app.routes.tiles import router as tiles_router

# ================================
# CREATE FASTAPI APP
# ================================
app = FastAPI(
    title="Drone-Based Deforestation Monitor",
    version="1.0.0"
)

# ================================
# GLOBAL STATE
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
# ROUTERS
# ================================
app.include_router(analyze_router)
app.include_router(jobs_router)
app.include_router(tiles_router)

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
def startup_event():
    threading.Thread(target=init_ee_background, daemon=True).start()

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
        "filename": file.filename,
        "size_mb": round(path.stat().st_size / (1024 * 1024), 2)
    }

# ================================
# ANALYSIS ENDPOINT
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
def get_job(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOB_STORE[job_id]
