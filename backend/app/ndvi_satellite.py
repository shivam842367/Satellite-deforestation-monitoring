import ee

def compute_satellite_ndvi(
    aoi_coords,
    start_date,
    end_date,
    threshold=0.15,
    collection="COPERNICUS/S2_SR_HARMONIZED"
):
    """
    Computes vegetation area (square meters) using NDVI.
    RETURNS ONLY A NUMBER. NO TILE URL. NO MAPID.
    """

    geometry = ee.Geometry.Polygon(aoi_coords)

    # Sentinel-2 bands
    nir_band = "B8"
    red_band = "B4"
    scale = 10

    collection = (
        ee.ImageCollection(collection)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
        .select([nir_band, red_band])
    )

    # No images found
    if collection.size().getInfo() == 0:
        return 0.0

    median_image = collection.median()

    ndvi = median_image.normalizedDifference(
        [nir_band, red_band]
    ).rename("NDVI")

    vegetation_mask = ndvi.gt(threshold)

    vegetation_area = vegetation_mask.multiply(
        ee.Image.pixelArea()
    )

    stats = vegetation_area.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True
    )

    area_sqm = stats.get("NDVI")

    if area_sqm is None:
        return 0.0

    return ee.Number(area_sqm).getInfo()
