import ee
import traceback
from typing import Dict
from app.ndvi_satellite import compute_satellite_ndvi
from app.ndvi_drone import process_drone_data_for_comparison


def calculate_deforestation_rate(past, present, years):
    if past <= 0 or years <= 0:
        return 0.0
    return round(((present - past) / past) / years * 100, 3)


def run_ndvi_job(job_id: str, payload: dict, job_store: Dict):
    try:
        geometry = payload["geometry"]["coordinates"]
        past_year = payload["past_year"]
        present_year = payload["present_year"]

        # -----------------------------
        # SATELLITE NDVI (ALWAYS RUNS)
        # -----------------------------
        past_area = compute_satellite_ndvi(
            geometry, f"{past_year}-01-01", f"{past_year}-12-31"
        ) or 0

        present_area = compute_satellite_ndvi(
            geometry, f"{present_year}-01-01", f"{present_year}-12-31"
        ) or 0

        past_ha = past_area / 10000
        present_ha = present_area / 10000

        result = {
            "satellite_comparison": {
                "past_year": past_year,
                "present_year": present_year,
                "past_cover_ha": round(past_ha, 2),
                "present_cover_ha": round(present_ha, 2),
                "change_ha": round(present_ha - past_ha, 2),
            }
        }

        # -----------------------------
        # DRONE DATA (OPTIONAL & SAFE)
        # -----------------------------
        if "drone_image_path" in payload:
            try:
                result["drone_data"] = process_drone_data_for_comparison(
                    payload["drone_image_path"],
                    {"type": "Polygon", "coordinates": geometry}
                )
            except Exception as drone_error:
                result["drone_data"] = {
                    "error": str(drone_error),
                    "vegetation_area_ha": None,
                    "total_area_ha": None,
                    "vegetation_percentage": None,
                    "mean_ndvi": None,
                }

        job_store[job_id]["status"] = "completed"
        job_store[job_id]["result"] = result

    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)
