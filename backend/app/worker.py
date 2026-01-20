import uuid
import ee
from app.jobs import jobs
from app.ndvi_satellite import compute_ndvi
from app.utils import sqm_to_hectares

def run_ndvi_job(job_id, payload):
    try:
        past = compute_ndvi(
            payload["aoi"],
            payload["past_start"],
            payload["past_end"],
            payload["threshold"]
        )
        present = compute_ndvi(
            payload["aoi"],
            payload["present_start"],
            payload["present_end"],
            payload["threshold"]
        )

        results = ee.Dictionary({
            "past": past,
            "present": present
        }).getInfo()

        past_ha = sqm_to_hectares(results["past"])
        present_ha = sqm_to_hectares(results["present"])

        jobs[job_id] = {
            "status": "completed",
            "past_cover_ha": round(past_ha, 2),
            "present_cover_ha": round(present_ha, 2),
            "change_ha": round(present_ha - past_ha, 2),
            "percent_change": round(
                ((present_ha - past_ha) / past_ha * 100) if past_ha else 0, 2
            )
        }

    except Exception as e:
        jobs[job_id] = {
            "status": "failed",
            "error": str(e)
        }
