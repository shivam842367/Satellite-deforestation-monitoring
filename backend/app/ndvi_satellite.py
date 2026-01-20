import ee

def compute_ndvi(aoi, start, end, threshold):
    geometry = ee.Geometry.Polygon(aoi)

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR")
        .filterBounds(geometry)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
    )

    image = collection.median()

    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    vegetation = ndvi.gt(threshold)

    area_image = vegetation.multiply(ee.Image.pixelArea())

    area_stats = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=10,
        maxPixels=1e13
    )

    return ee.Number(area_stats.get("NDVI", 0))
