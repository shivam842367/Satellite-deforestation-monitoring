import ee


def compute_satellite_ndvi(
    aoi_coords,
    start_date,
    end_date,
    threshold=0.15,
    collection="COPERNICUS/S2_SR_HARMONIZED"
):
    geometry = ee.Geometry.Polygon(aoi_coords)

    # Band configuration
    if "COPERNICUS/S2" in collection:
        nir_band = "B8"
        red_band = "B4"
        cloud_property = "CLOUDY_PIXEL_PERCENTAGE"
        scale = 10
    else:
        nir_band = "SR_B5"
        red_band = "SR_B4"
        cloud_property = "CLOUD_COVER"
        scale = 30

    # Load and filter imagery
    img_collection = (
        ee.ImageCollection(collection)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt(cloud_property, 40))
        .select([nir_band, red_band])
    )

    # No imagery case
    if img_collection.size().getInfo() == 0:
        return ee.Number(0)

    # Median composite
    median_image = img_collection.median()

    # NDVI computation
    ndvi = median_image.normalizedDifference([nir_band, red_band]).rename("ndvi")

    # Vegetation mask (CRITICAL)
    vegetation_mask = ndvi.gt(threshold).selfMask()

    # Pixel area in square meters
    pixel_area = ee.Image.pixelArea()

    # Vegetation area image (named band!)
    vegetation_area_image = vegetation_mask.multiply(pixel_area).rename("veg_area")

    # Reduce over AOI
    area_stats = vegetation_area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True
    )

    # Area in square meters → hectares
    vegetation_area_ha = ee.Number(area_stats.get("veg_area")).divide(10000)

    return vegetation_area_ha
