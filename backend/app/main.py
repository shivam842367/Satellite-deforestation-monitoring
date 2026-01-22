# app/main.py
"""
Enhanced Drone-Based Deforestation Monitoring API
Multi-source comparison: Past Satellite → Present Satellite → Drone
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional
import uuid
import json
from pathlib import Path
import shutil

from app.schemas import NDVIRequest
from app.worker import run_ndvi_job
from app.ee_client import init_ee

# ==========================================
# GLOBAL JOB STORE
# ==========================================
JOB_STORE: Dict[str, dict] = {}

# ==========================================
# DATA DIRECTORY FOR UPLOADED DRONE IMAGES
# ==========================================
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# APP INITIALIZATION
# ==========================================
app = FastAPI(
    title="Drone-Based Deforestation Monitoring API",
    version="2.0.0",
    description="Multi-source vegetation analysis: Satellite (past/present) + Drone (current)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# STARTUP: EARTH ENGINE INIT
# ==========================================
@app.on_event("startup")
def startup_event():
    try:
        init_ee()
        print("✅ Earth Engine initialized successfully.")
    except Exception as e:
        print(f"⚠️ Earth Engine init failed: {e}")
        print("   Continuing without Earth Engine (drone-only mode available)")

# ==========================================
# HEALTH CHECK
# ==========================================
@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "Deforestation Monitoring API v2.0",
        "features": [
            "Satellite data comparison (Earth Engine)",
            "Drone data processing & downscaling",
            "Multi-temporal analysis"
        ]
    }

# ==========================================
# UPLOAD DRONE IMAGE
# ==========================================
@app.post("/upload-drone-image")
async def upload_drone_image(file: UploadFile = File(...)):
    """
    Upload drone multispectral image (GeoTIFF)
    Expected bands: [Red, Green, Blue, NIR] or specify custom bands
    
    Returns:
        file_id: Unique identifier for uploaded file
        path: Server path (internal use)
    """
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        save_path = UPLOAD_DIR / f"{file_id}{file_extension}"
        
        # Save file
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "path": str(save_path),
            "size_mb": round(save_path.stat().st_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ==========================================
# ANALYZE (MULTI-SOURCE)
# ==========================================
@app.post("/analyze")
async def analyze(
    req: NDVIRequest,
    bg: BackgroundTasks,
    drone_image_id: Optional[str] = None
):
    """
    Submit comprehensive deforestation analysis job
    
    Workflow:
    1. Past satellite data (e.g., 2016 Landsat)
    2. Present satellite data (e.g., 2024 Sentinel-2)
    3. Current drone data (optional, high-res → downscaled)
    4. Calculate trends and rates
    
    Args:
        req: Request with geometry, past_year, present_year
        drone_image_id: Optional file_id from /upload-drone-image
    
    Returns:
        job_id: For polling /jobs/{job_id}
    """
    job_id = str(uuid.uuid4())
    
    # Initialize job state
    JOB_STORE[job_id] = {
        "status": "processing",
        "result": None,
        "error": None
    }
    
    # Prepare payload
    payload = req.dict()
    
    # Add drone image path if provided
    if drone_image_id:
        drone_path = UPLOAD_DIR / f"{drone_image_id}.tif"  # Adjust extension as needed
        
        if not drone_path.exists():
            # Try to find file with any extension
            matching_files = list(UPLOAD_DIR.glob(f"{drone_image_id}.*"))
            if matching_files:
                drone_path = matching_files[0]
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Drone image not found: {drone_image_id}"
                )
        
        payload["drone_image_path"] = str(drone_path)
    
    # Launch background task
    bg.add_task(
        run_ndvi_job,
        job_id,
        payload,
        JOB_STORE
    )
    
    return {
        "job_id": job_id,
        "status": "submitted",
        "includes_drone_data": drone_image_id is not None
    }

# ==========================================
# JOB STATUS / RESULT POLLING
# ==========================================
@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    """
    Poll job status and retrieve results
    
    Returns:
        status: "processing" | "completed" | "failed"
        satellite_comparison: Past vs Present satellite data
        drone_data: Drone analysis results (if provided)
        summary: Overall statistics
    """
    job = JOB_STORE.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job ID not found"
        )
    
    return {
        "job_id": job_id,
        **job
    }

# ==========================================
# DEMO MODE (NO DEPENDENCIES)
# ==========================================
@app.post("/analyze-demo")
def analyze_demo():
    """
    Stable demo endpoint with synthetic data
    Useful for frontend testing without backend dependencies
    """
    return {
        "satellite_comparison": {
            "past_year": 2016,
            "past_cover_ha": 120.5,
            "present_year": 2024,
            "present_cover_ha": 95.2,
            "change_ha": -25.3,
            "deforestation_rate_pct_per_year": -2.63
        },
        "drone_data": {
            "vegetation_area_ha": 92.8,
            "total_area_ha": 130.0,
            "vegetation_percentage": 71.4,
            "mean_ndvi": 0.62,
            "original_resolution_m": 0.05,
            "downscaled_resolution_m": 10.0,
            "comparison_with_satellite": {
                "difference_from_present_satellite_ha": -2.4,
                "recent_trend_rate_pct_per_year": -2.52
            }
        },
        "summary": {
            "total_loss_ha": 25.3,
            "total_loss_pct": 21.0,
            "time_period_years": 8
        },
        "mode": "demo"
    }

# ==========================================
# LIST UPLOADED FILES
# ==========================================
@app.get("/uploads")
def list_uploads():
    """List all uploaded drone images"""
    files = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            files.append({
                "file_id": file_path.stem,
                "filename": file_path.name,
                "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2)
            })
    
    return {"files": files, "count": len(files)}

# ==========================================
# DELETE UPLOADED FILE
# ==========================================
@app.delete("/uploads/{file_id}")
def delete_upload(file_id: str):
    """Delete an uploaded drone image"""
    matching_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    
    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    matching_files[0].unlink()
    
    return {"message": "File deleted successfully", "file_id": file_id}