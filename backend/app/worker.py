import ee
from app.jobs import jobs
from app.ndvi_satellite import compute_ndvi
from app.utils import sqm_to_hectares

def run_ndvi_job(job_id, payload):
    try:
        # -----------------------------
        # Extract inputs
        # -----------------------------
        aoi_geojson = payload["aoi"]

        # Defensive handling (Feature or FeatureCollection)
        if aoi_geojson["type"] == "FeatureCollection":
            aoi_geojson = aoi_geojson["features"][0]

        coords = aoi_geojson["geometry"]["coordinates"]

        past_year = payload["past_year"]
        present_year = payload["present_year"]

        past_start = f"{past_year}-01-01"
        past_end = f"{past_year}-12-31"

        present_start = f"{present_year}-01-01"
        present_end = f"{present_year}-12-31"

        threshold = 0.4  # fixed NDVI threshold (stable)

        # -----------------------------
        # NDVI computation
        # -----------------------------
        past = compute_ndvi(coords, past_start, past_end, threshold)
        present = compute_ndvi(coords, present_start, present_end, threshold)

        results = ee.Dictionary({
            "past": past,
            "present": present
        }).getInfo()

        # -----------------------------
        # Area conversion
        # -----------------------------
        past_ha = sqm_to_hectares(results["past"])
        present_ha = sqm_to_hectares(results["present"])

        rate = (
            ((present_ha - past_ha) / past_ha) / (present_year - past_year) * 100
            if past_ha > 0 else 0
        )

        jobs[job_id] = {
            "status": "completed",
            "past_cover_ha": round(past_ha, 2),
            "present_cover_ha": round(present_ha, 2),
            "deforestation_rate_pct_per_year": round(rate, 2),
            "years": {
                "past": past_year,
                "present": present_year
            }
        }

    except Exception as e:
        jobs[job_id] = {
            "status": "failed",
            "error": str(e)
        }
