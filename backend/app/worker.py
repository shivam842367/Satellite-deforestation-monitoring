import ee
from app.ndvi_satellite import compute_ndvi
from app.utils import sqm_to_hectares


def run_ndvi_job(job_id: str, payload: dict, job_store: dict):
    """
    Background NDVI processing job.
    Updates shared job_store in-place.
    """

    try:
        # -------------------------------------------------
        # 1. Extract geometry (GeoJSON Polygon)
        # -------------------------------------------------
        geometry = payload["geometry"]

        if geometry["type"] not in ("Polygon", "MultiPolygon"):
            raise ValueError("Only Polygon / MultiPolygon geometries are supported")

        coords = geometry["coordinates"]

        # -------------------------------------------------
        # 2. Time range
        # -------------------------------------------------
        past_year = payload["past_year"]
        present_year = payload["present_year"]

        past_start = f"{past_year}-01-01"
        past_end = f"{past_year}-12-31"

        present_start = f"{present_year}-01-01"
        present_end = f"{present_year}-12-31"

        threshold = payload.get("threshold", 0.4)

        # -------------------------------------------------
        # 3. NDVI computation (Earth Engine)
        # -------------------------------------------------
        past_area_sqm = compute_ndvi(
            coords=coords,
            start_date=past_start,
            end_date=past_end,
            threshold=threshold
        )

        present_area_sqm = compute_ndvi(
            coords=coords,
            start_date=present_start,
            end_date=present_end,
            threshold=threshold
        )

        # -------------------------------------------------
        # 4. Convert to hectares
        # -------------------------------------------------
        past_ha = sqm_to_hectares(past_area_sqm)
        present_ha = sqm_to_hectares(present_area_sqm)

        # -------------------------------------------------
        # 5. Change & rate calculation
        # -------------------------------------------------
        delta_ha = present_ha - past_ha

        years = max(present_year - past_year, 1)

        rate_pct_per_year = (
            (delta_ha / past_ha) * 100 / years
            if past_ha > 0 else 0
        )

        # -------------------------------------------------
        # 6. Update job store (SUCCESS)
        # -------------------------------------------------
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["result"] = {
            "past_cover_ha": round(past_ha, 2),
            "present_cover_ha": round(present_ha, 2),
            "change_ha": round(delta_ha, 2),
            "deforestation_rate_pct_per_year": round(rate_pct_per_year, 2),
            "years": {
                "past": past_year,
                "present": present_year
            }
        }

    except Exception as e:
        # -------------------------------------------------
        # 7. Update job store (FAILURE)
        # -------------------------------------------------
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)
