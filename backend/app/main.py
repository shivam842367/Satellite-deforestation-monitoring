from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid

from app.schemas import NDVIRequest
from app.jobs import jobs
from app.worker import run_ndvi_job
from app.ee_client import init_ee

"""
DESIGN OVERVIEW
---------------
• Earth Engine initialized ONCE at startup
• /analyze is non-blocking (background job)
• /result/{job_id} is used for polling
• /analyze-demo provides stable fallback
• Safe for Fly.io + GDAL
"""

# -------------------------------------------------------------------
# APP INITIALIZATION
# -------------------------------------------------------------------

app = FastAPI(
    title="Drone-Based Deforestation Monitoring API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# STARTUP: EARTH ENGINE INIT (CRITICAL)
# -------------------------------------------------------------------

@app.on_event("startup")
def startup_event():
    """
    Initialize Earth Engine once for the entire app.
    Fail fast if credentials are invalid.
    """
    try:
        init_ee()
        print("Earth Engine initialized successfully.")
    except Exception as e:
        raise RuntimeError(f"Earth Engine init failed: {e}")

# -------------------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------------------

@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "Deforestation Monitoring API",
        "ee": "initialized"
    }

# -------------------------------------------------------------------
# ANALYZE ENDPOINT (ASYNC SAFE)
# -------------------------------------------------------------------

@app.post("/analyze")
def analyze(req: NDVIRequest, bg: BackgroundTasks):
    """
    Starts a deforestation analysis job.

    • Returns immediately with job_id
    • EE + GDAL run in background
    • Frontend polls /result/{job_id}
    """

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status": "processing"
    }

    bg.add_task(run_ndvi_job, job_id, req.dict())

    return {
        "job_id": job_id,
        "status": "submitted"
    }

# -------------------------------------------------------------------
# RESULT POLLING ENDPOINT
# -------------------------------------------------------------------

@app.get("/result/{job_id}")
def get_result(job_id: str):
    """
    Returns job status or final result.
    """

    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail="Job ID not found"
        )

    return jobs[job_id]

# -------------------------------------------------------------------
# STABLE DEMO MODE ENDPOINT (OPTIONAL)
# -------------------------------------------------------------------

@app.post("/analyze-demo")
def analyze_demo():
    """
    Stable, synchronous demo endpoint.
    Useful for UI testing or fallback demos.
    """

    past_cover_ha = 120.5
    present_cover_ha = 95.2

    change_ha = present_cover_ha - past_cover_ha
    percent_change = (
        (change_ha / past_cover_ha) * 100
        if past_cover_ha > 0 else 0
    )

    return {
        "past_cover_ha": round(past_cover_ha, 2),
        "present_cover_ha": round(present_cover_ha, 2),
        "change_ha": round(change_ha, 2),
        "percent_change": round(percent_change, 2),
        "mode": "stable-demo"
    }
