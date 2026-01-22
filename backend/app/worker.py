# app/worker.py
"""
Enhanced Worker for Multi-Source Deforestation Analysis
Compares: Past Satellite → Present Satellite → Current Drone Data
"""

import ee
from typing import Dict
import traceback
from app.ndvi_satellite import compute_satellite_ndvi
from app.ndvi_drone import process_drone_data_for_comparison
from app.utils import sqm_to_hectares


def calculate_deforestation_rate(
    past_area_ha: float,
    present_area_ha: float,
    years_elapsed: float
) -> float:
    """
    Calculate annual deforestation rate
    
    Args:
        past_area_ha: Vegetation area in past (hectares)
        present_area_ha: Vegetation area in present (hectares)
        years_elapsed: Time period in years
        
    Returns:
        Annual deforestation rate as percentage
    """
    if past_area_ha <= 0 or years_elapsed <= 0:
        return 0.0
        
    # Annual rate = (change / initial) / years * 100
    change_ha = present_area_ha - past_area_ha
    rate = (change_ha / past_area_ha) / years_elapsed * 100
    
    return round(rate, 3)


def run_ndvi_job(job_id: str, payload: dict, job_store: Dict):
    """
    Complete analysis pipeline:
    1. Past satellite data (e.g., 2016)
    2. Present satellite data (e.g., 2024)
    3. Current drone data (high-res, downscaled to satellite)
    4. Calculate deforestation trends
    
    Args:
        job_id: Unique job identifier
        payload: Request payload with geometry, years, drone_image_path
        job_store: In-memory job storage
    """
    try:
        job_store[job_id]["status"] = "processing"
        
        # ==========================================
        # EXTRACT PARAMETERS
        # ==========================================
        geometry = payload["geometry"]
        coords = geometry["coordinates"]
        
        past_year = payload.get("past_year", 2016)
        present_year = payload.get("present_year", 2024)
        
        # Optional: drone image path (if provided)
        drone_image_path = payload.get("drone_image_path", None)
        
        # ==========================================
        # 1. PAST SATELLITE DATA
        # ==========================================
        past_start = f"{past_year}-01-01"
        past_end = f"{past_year}-12-31"
        
        past_area_sqm = compute_satellite_ndvi(
            coords,
            past_start,
            past_end,
            threshold=0.4,
            collection="COPERNICUS/S2_SR"  # or LANDSAT for older data
        )
        
        past_area_sqm_value = ee.Number(past_area_sqm).getInfo()
        past_cover_ha = sqm_to_hectares(past_area_sqm_value)
        
        # ==========================================
        # 2. PRESENT SATELLITE DATA
        # ==========================================
        present_start = f"{present_year}-01-01"
        present_end = f"{present_year}-12-31"
        
        present_area_sqm = compute_satellite_ndvi(
            coords,
            present_start,
            present_end,
            threshold=0.4,
            collection="COPERNICUS/S2_SR"
        )
        
        present_area_sqm_value = ee.Number(present_area_sqm).getInfo()
        present_cover_ha = sqm_to_hectares(present_area_sqm_value)
        
        # ==========================================
        # 3. SATELLITE DEFORESTATION RATE
        # ==========================================
        years_elapsed = present_year - past_year
        satellite_rate = calculate_deforestation_rate(
            past_cover_ha,
            present_cover_ha,
            years_elapsed
        )
        
        # ==========================================
        # 4. DRONE DATA (IF PROVIDED)
        # ==========================================
        drone_results = None
        
        if drone_image_path:
            try:
                # Convert coordinates to GeoJSON format
                aoi_geojson = {
                    "type": "Polygon",
                    "coordinates": coords
                }
                
                drone_results = process_drone_data_for_comparison(
                    drone_image_path,
                    aoi_geojson,
                    red_band=0,
                    nir_band=3
                )
                
                drone_cover_ha = drone_results['drone_stats']['vegetation_area_ha']
                
                # Calculate trend: Satellite Present → Drone Current
                # Assuming drone data is from current year (present_year or later)
                drone_rate = calculate_deforestation_rate(
                    present_cover_ha,
                    drone_cover_ha,
                    1.0  # Assume 1 year difference or adjust as needed
                )
                
            except Exception as drone_error:
                print(f"⚠️ Drone processing failed: {drone_error}")
                drone_results = {
                    "error": str(drone_error),
                    "trace": traceback.format_exc()
                }
        
        # ==========================================
        # 5. COMPILE RESULTS
        # ==========================================
        result = {
            "status": "completed",
            
            # Satellite comparison (past → present)
            "satellite_comparison": {
                "past_year": past_year,
                "past_cover_ha": round(past_cover_ha, 2),
                "present_year": present_year,
                "present_cover_ha": round(present_cover_ha, 2),
                "change_ha": round(present_cover_ha - past_cover_ha, 2),
                "deforestation_rate_pct_per_year": satellite_rate
            },
            
            # Drone data (if available)
            "drone_data": None,
            
            # Overall summary
            "summary": {
                "total_loss_ha": round(past_cover_ha - present_cover_ha, 2),
                "total_loss_pct": round(
                    ((past_cover_ha - present_cover_ha) / past_cover_ha * 100) 
                    if past_cover_ha > 0 else 0,
                    2
                ),
                "time_period_years": years_elapsed
            }
        }
        
        # Add drone results if available
        if drone_results and "error" not in drone_results:
            result["drone_data"] = {
                "vegetation_area_ha": drone_results['drone_stats']['vegetation_area_ha'],
                "total_area_ha": drone_results['drone_stats']['total_area_ha'],
                "vegetation_percentage": drone_results['drone_stats']['vegetation_percentage'],
                "mean_ndvi": drone_results['drone_stats']['mean_ndvi'],
                "original_resolution_m": drone_results['original_resolution_m'],
                "downscaled_resolution_m": drone_results['downscaled_resolution_m'],
                
                # Comparison with satellite
                "comparison_with_satellite": {
                    "difference_from_present_satellite_ha": round(
                        drone_results['drone_stats']['vegetation_area_ha'] - present_cover_ha,
                        2
                    ),
                    "recent_trend_rate_pct_per_year": drone_rate if 'drone_rate' in locals() else 0
                }
            }
        elif drone_results and "error" in drone_results:
            result["drone_data"] = {
                "status": "failed",
                "error": drone_results["error"]
            }
        
        # Store completed job
        job_store[job_id] = result
        
    except Exception as e:
        job_store[job_id] = {
            "status": "failed",
            "error": str(e),
            "trace": traceback.format_exc()
        }