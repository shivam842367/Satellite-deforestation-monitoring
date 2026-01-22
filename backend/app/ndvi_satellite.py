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

    nir = "B8"
    red = "B4"
    scale = 10

    collection = (
        ee.ImageCollection(collection)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
        .select([nir, red])
    )

    if collection.size().getInfo() == 0:
        if return_map:
            return 0, None, None
        return 0

    image = collection.median()

    ndvi = image.normalizedDifference([nir, red]).rename("NDVI")

    # ---- Area calculation ----
    veg = ndvi.gt(threshold)
    area_img = veg.multiply(ee.Image.pixelArea())

    area = area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13
    ).get("NDVI")

    area = ee.Number(area)

    if not return_map:
        return area

    # ---- NDVI tiles ----
    vis = {
        "min": 0.0,
        "max": 0.8,
        "palette": ["brown", "yellow", "green"]
    }

    map_id = ndvi.getMapId(vis)
    tile_url = map_id["tile_fetcher"].url_format

    # ---- Histogram ----
    hist = ndvi.reduceRegion(
        reducer=ee.Reducer.histogram(20),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13
    ).get("NDVI")

    return area, tile_url, hist
