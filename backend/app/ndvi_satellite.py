# app/ndvi_satellite.py
"""
Enhanced Satellite Data Processing with Earth Engine
Supports both Sentinel-2 and Landsat collections
"""

import ee
from typing import List


def compute_satellite_ndvi(
    aoi_coords: List[List[List[float]]],
    start_date: str,
    end_date: str,
    threshold: float = 0.4,
    collection: str = "COPERNICUS/S2_SR"
) -> ee.Number:
    """
    Compute vegetation area from satellite imagery using Earth Engine
    
    Args:
        aoi_coords: Polygon coordinates [[[lon, lat], ...]]
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        threshold: NDVI threshold for vegetation classification
        collection: Satellite collection ID
                   - "COPERNICUS/S2_SR" for Sentinel-2 (2015+)
                   - "LANDSAT/LC08/C02/T1_L2" for Landsat 8 (2013+)
                   - "LANDSAT/LE07/C02/T1_L2" for Landsat 7 (1999-2021)
    
    Returns:
        Vegetation area in square meters
    """
    # Create geometry
    geometry = ee.Geometry.Polygon(aoi_coords)
    
    # Select appropriate bands based on collection
    if "COPERNICUS/S2" in collection:
        # Sentinel-2: B8 (NIR), B4 (Red)
        nir_band = "B8"
        red_band = "B4"
        cloud_property = "CLOUDY_PIXEL_PERCENTAGE"
        scale = 10  # 10m resolution
        
    elif "LANDSAT/LC08" in collection or "LANDSAT/LE07" in collection:
        # Landsat 8/7: SR_B5 (NIR), SR_B4 (Red)
        nir_band = "SR_B5"
        red_band = "SR_B4"
        cloud_property = "CLOUD_COVER"
        scale = 30  # 30m resolution
        
    else:
        raise ValueError(f"Unsupported collection: {collection}")
    
    # Filter collection
    img_collection = (
        ee.ImageCollection(collection)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt(cloud_property, 20))
    )
    
    # Check if collection is empty
    count = img_collection.size().getInfo()
    if count == 0:
        print(f"⚠️ No images found for {start_date} to {end_date}")
        return ee.Number(0)
    
    # Compute median composite
    median_image = img_collection.median()
    
    # Calculate NDVI
    ndvi = median_image.normalizedDifference([nir_band, red_band]).rename("NDVI")
    
    # Classify vegetation
    vegetation_mask = ndvi.gt(threshold)
    
    # Calculate area
    area_image = vegetation_mask.multiply(ee.Image.pixelArea())
    
    area_stats = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True
    )
    
    return ee.Number(area_stats.get("NDVI", 0))


def get_ndvi_image_for_visualization(
    aoi_coords: List[List[List[float]]],
    start_date: str,
    end_date: str,
    collection: str = "COPERNICUS/S2_SR"
) -> dict:
    """
    Generate NDVI visualization parameters for Google Earth Engine
    
    Returns:
        Dictionary with map tile URL and visualization parameters
    """
    geometry = ee.Geometry.Polygon(aoi_coords)
    
    # Select bands based on collection
    if "COPERNICUS/S2" in collection:
        nir_band, red_band = "B8", "B4"
        cloud_property = "CLOUDY_PIXEL_PERCENTAGE"
    else:
        nir_band, red_band = "SR_B5", "SR_B4"
        cloud_property = "CLOUD_COVER"
    
    # Get median composite
    img_collection = (
        ee.ImageCollection(collection)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt(cloud_property, 20))
    )
    
    median_image = img_collection.median()
    ndvi = median_image.normalizedDifference([nir_band, red_band])
    
    # Get map ID for visualization
    vis_params = {
        'min': -0.2,
        'max': 0.8,
        'palette': ['red', 'yellow', 'green']
    }
    
    map_id = ndvi.getMapId(vis_params)
    
    return {
        'tile_url': map_id['tile_fetcher'].url_format,
        'vis_params': vis_params
    }