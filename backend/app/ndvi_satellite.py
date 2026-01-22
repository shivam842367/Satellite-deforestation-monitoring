import ee

def compute_satellite_ndvi_pair(
    aoi_coords,
    past_range,
    present_range,
    collection="COPERNICUS/S2_SR_HARMONIZED"
):
    geometry = ee.Geometry.Polygon(aoi_coords)

    def get_ndvi(start, end):
        images = (
            ee.ImageCollection(collection)
            .filterBounds(geometry)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
            .select(["B8", "B4"])
        )

        if images.size().getInfo() == 0:
            return None

        median = images.median()
        return median.normalizedDifference(["B8", "B4"]).rename("NDVI")

    past_ndvi = get_ndvi(*past_range)
    present_ndvi = get_ndvi(*present_range)

    if past_ndvi is None or present_ndvi is None:
        return None

    diff_ndvi = present_ndvi.subtract(past_ndvi).rename("ΔNDVI")

    return past_ndvi, present_ndvi, diff_ndvi, geometry
