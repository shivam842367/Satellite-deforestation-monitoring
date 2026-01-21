from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
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
# STARTUP: EARTH ENGINE INIT
# -------------------------------------------------------------------

@app.on_event("startup")
def startup_event():
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
# ANALYZE ENDPOINT (PRODUCTION)
# -------------------------------------------------------------------
from fastapi import Request

@app.post("/debug/analyze-raw")
async def debug_analyze_raw(request: Request):
    body = await request.json()
    print("RAW BODY FROM FRONTEND:", body)
    return body

@app.post("/analyze")
async def analyze(
    req: NDVIRequest,
    bg: BackgroundTasks,
    request: Request
):
    """
    Starts a deforestation analysis job.
    """

    # 🔍 Safe request logging (after validation)
    print("VALIDATED REQUEST:", req.dict())

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
    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail="Job ID not found"
        )

    return jobs[job_id]

# -------------------------------------------------------------------
# DEBUG ENDPOINT (RAW BODY – OPTIONAL)
# -------------------------------------------------------------------

@app.post("/debug/analyze-raw")
async def analyze_raw(request: Request):
    """
    Debug-only endpoint to inspect raw JSON payload.
    Does NOT use schema validation.
    """
    body = await request.json()
    print("RAW REQUEST BODY:", body)
    return {"received": body}

# -------------------------------------------------------------------
# STABLE DEMO MODE
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
