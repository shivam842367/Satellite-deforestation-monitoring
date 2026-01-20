import rasterio
import numpy as np
from rasterio.mask import mask

def compute_ndvi_stats(aoi_geojson):
    # ---- PAST (LANDSAT 2016) ----
    with rasterio.open("data/landsat_2016.tif") as src:
        past, transform = mask(src, [aoi_geojson], crop=True)
        red_p = past[0].astype(float)
        nir_p = past[1].astype(float)
        pixel_area = abs(transform.a * transform.e)

    # ---- PRESENT (SENTINEL 2024) ----
    with rasterio.open("data/sentinel_2024.tif") as src:
        pres, transform = mask(src, [aoi_geojson], crop=True)
        red_c = pres[0].astype(float)
        nir_c = pres[1].astype(float)

    ndvi_p = (nir_p - red_p) / (nir_p + red_p + 1e-6)
    ndvi_c = (nir_c - red_c) / (nir_c + red_c + 1e-6)

    veg_p = ndvi_p > 0.4
    veg_c = ndvi_c > 0.4

    area_p = veg_p.sum() * pixel_area / 10_000
    area_c = veg_c.sum() * pixel_area / 10_000

    rate = ((area_p - area_c) / area_p) * (100 / 8)

    return {
        "past_cover_ha": round(area_p, 2),
        "present_cover_ha": round(area_c, 2),
        "deforestation_rate_pct_per_year": round(rate, 2)
    }
