import ee
from typing import List


def compute_satellite_ndvi(
    aoi_coords: List[List[List[float]]],
    start_date: str,
    end_date: str,
    threshold: float = 0.4,
    collection: str = "COPERNICUS/S2_SR"
) -> ee.Number:

    geometry = ee.Geometry.Polygon(aoi_coords)

    if "COPERNICUS/S2" in collection:
        nir, red = "B8", "B4"
        cloud = "CLOUDY_PIXEL_PERCENTAGE"
        scale = 10
    else:
        nir, red = "SR_B5", "SR_B4"
        cloud = "CLOUD_COVER"
        scale = 30

    images = (
        ee.ImageCollection(collection)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt(cloud, 40))
    )

    if images.size().getInfo() == 0:
        return ee.Number(0)

    ndvi = images.median().normalizedDifference([nir, red])

    vegetation = ndvi.gt(threshold)
    area = vegetation.multiply(ee.Image.pixelArea())

    stats = area.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13
    )

    return ee.Number(stats.get("NDVI", 0))
