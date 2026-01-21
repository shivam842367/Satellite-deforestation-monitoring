from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uuid

from app.schemas import NDVIRequest
from app.worker import run_ndvi_job
from app.ee_client import init_ee

"""
DESIGN OVERVIEW
---------------
• Earth Engine initialized ONCE at startup
• /analyze submits async NDVI job
• /jobs/{job_id} is used for polling
• In-memory job store (sufficient for demo & academic use)
"""

# -------------------------------------------------------------------
# GLOBAL JOB STORE
# -------------------------------------------------------------------

JOB_STORE: Dict[str, dict] = {}

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
# STARTUP: EARTH ENGINE INIT
# -------------------------------------------------------------------

@app.on_event("startup")
def startup_event():
    try:
        init_ee()
        print("✅ Earth Engine initialized successfully.")
    except Exception as e:
        raise RuntimeError(f"❌ Earth Engine init failed: {e}")

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
# DEBUG ENDPOINT (RAW JSON – OPTIONAL)
# -------------------------------------------------------------------

@app.post("/debug/analyze-raw")
async def debug_analyze_raw(request: Request):
    body = await request.json()
    print("🧪 RAW REQUEST BODY:", body)
    return {"received": body}

# -------------------------------------------------------------------
# ANALYZE ENDPOINT (ASYNC – PRODUCTION)
# -------------------------------------------------------------------

@app.post("/analyze")
async def analyze(
    req: NDVIRequest,
    bg: BackgroundTasks
):
    """
    Submits a deforestation analysis job.
    Non-blocking. Use /jobs/{job_id} to poll.
    """

    job_id = str(uuid.uuid4())

    # Initialize job state
    JOB_STORE[job_id] = {
        "status": "processing",
        "result": None,
        "error": None
    }

    # Launch background task
    bg.add_task(
        run_ndvi_job,
        job_id,
        req.dict(),
        JOB_STORE
    )

    return {
        "job_id": job_id,
        "status": "submitted"
    }

# -------------------------------------------------------------------
# JOB STATUS / RESULT POLLING
# -------------------------------------------------------------------

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = JOB_STORE.get(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job ID not found"
        )

    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job["result"],
        "error": job["error"]
    }

# -------------------------------------------------------------------
# STABLE DEMO MODE (NO EE DEPENDENCY)
# -------------------------------------------------------------------

@app.post("/analyze-demo")
def analyze_demo():
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
