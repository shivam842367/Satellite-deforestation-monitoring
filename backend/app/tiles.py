import ee
from app.ndvi_satellite import get_sentinel_ndvi


def get_ndvi_difference_tile(aoi_coords, past_year, present_year):
    """
    Returns a tile URL for NDVI difference (present - past)
    """
    aoi = ee.Geometry.Polygon(aoi_coords)

    ndvi_past = get_sentinel_ndvi(aoi, past_year)
    ndvi_present = get_sentinel_ndvi(aoi, present_year)

    ndvi_diff = ndvi_present.subtract(ndvi_past).clip(aoi)

    vis_params = {
        "min": -0.5,
        "max": 0.5,
        "palette": [
            "#8e0000",  # strong loss
            "#ff4d4d",  # moderate loss
            "#ffffff",  # no change
            "#7bed9f",  # moderate gain
            "#1e8449",  # strong gain
        ],
    }

    map_id = ndvi_diff.getMapId(vis_params)

    return map_id["tile_fetcher"].url_format
