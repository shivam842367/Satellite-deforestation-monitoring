import ee

def compute_ndvi_difference_tile(
    aoi_coords,
    past_start_date,
    past_end_date,
    present_start_date,
    present_end_date,
    collection="COPERNICUS/S2_SR_HARMONIZED"
):
    """
    Computes NDVI difference (present - past) and returns
    an Earth Engine tile URL for visualization.
    """

    geometry = ee.Geometry.Polygon(aoi_coords)

    nir_band = "B8"
    red_band = "B4"

    def get_ndvi(start_date, end_date):
        col = (
            ee.ImageCollection(collection)
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
            .select([nir_band, red_band])
        )

        return col.median().normalizedDifference(
            [nir_band, red_band]
        ).rename("NDVI")

    # NDVI for both periods
    ndvi_past = get_ndvi(past_start_date, past_end_date)
    ndvi_present = get_ndvi(present_start_date, present_end_date)

    # NDVI Difference
    ndvi_diff = ndvi_present.subtract(ndvi_past).clip(geometry)

    # Visualization parameters (scientifically sane)
    vis_params = {
        "min": -0.4,
        "max": 0.4,
        "palette": [
            "#8e0000",  # severe loss
            "#ff4d4d",  # moderate loss
            "#ffffff",  # no change
            "#7bed9f",  # moderate gain
            "#1e8449",  # strong gain
        ],
    }

    map_id = ndvi_diff.getMapId(vis_params)

    return map_id["tile_fetcher"].url_format
