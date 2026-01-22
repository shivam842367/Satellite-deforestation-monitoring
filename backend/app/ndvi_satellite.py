import ee
def compute_satellite_ndvi(
    aoi_coords,
    start_date,
    end_date,
    threshold=0.15,
    collection="COPERNICUS/S2_SR_HARMONIZED",
    return_map=False
):
    geometry = ee.Geometry.Polygon(aoi_coords)

    nir_band = "B8"
    red_band = "B4"
    scale = 10

    img_collection = (
        ee.ImageCollection(collection)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
        .select([nir_band, red_band])
    )

    if img_collection.size().getInfo() == 0:
        if return_map:
            return 0, None
        return 0

    median_image = img_collection.median()

    ndvi = median_image.normalizedDifference(
        [nir_band, red_band]
    ).rename("NDVI")

    # ---- AREA COMPUTATION (UNCHANGED) ----
    vegetation = ndvi.gt(threshold)
    area_image = vegetation.multiply(ee.Image.pixelArea())

    area_stats = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True
    )

    area = ee.Number(area_stats.get("NDVI", 0))

    # ---- MAP TILE EXPORT (NEW) ----
    if return_map:
        vis = {
            "min": 0.0,
            "max": 0.8,
            "palette": ["brown", "yellow", "green"]
        }

        map_id = ndvi.getMapId(vis)
        tile_url = map_id["tile_fetcher"].url_format

        return area, tile_url

    return area
