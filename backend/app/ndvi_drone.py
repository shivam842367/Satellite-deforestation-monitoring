# app/ndvi_drone.py
"""
Drone-Based NDVI Computation & Downscaling
Processes high-resolution drone imagery and aligns it with satellite resolution
"""

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
from rasterio.mask import mask
from rasterio.enums import Resampling as ResamplingEnum
from typing import Dict, Tuple
import cv2
from pathlib import Path


class DroneNDVIProcessor:
    """
    Handles drone imagery processing:
    1. NDVI calculation from multispectral drone data
    2. Downscaling to satellite resolution (10m for Sentinel-2)
    3. Alignment with satellite imagery
    """
    
    def __init__(self, satellite_resolution: float = 10.0):
        """
        Args:
            satellite_resolution: Target resolution in meters (default 10m for Sentinel-2)
        """
        self.satellite_resolution = satellite_resolution
        
    def compute_drone_ndvi(
        self, 
        drone_image_path: str,
        red_band_idx: int = 0,
        nir_band_idx: int = 3
    ) -> Tuple[np.ndarray, dict]:
        """
        Calculate NDVI from drone multispectral imagery
        
        Args:
            drone_image_path: Path to drone GeoTIFF (bands: R, G, B, NIR)
            red_band_idx: Index of red band (default: 0)
            nir_band_idx: Index of NIR band (default: 3)
            
        Returns:
            ndvi: NDVI array
            metadata: Rasterio metadata
        """
        with rasterio.open(drone_image_path) as src:
            red = src.read(red_band_idx + 1).astype(float)
            nir = src.read(nir_band_idx + 1).astype(float)
            metadata = src.meta.copy()
            
            # Calculate NDVI: (NIR - Red) / (NIR + Red)
            ndvi = np.where(
                (nir + red) == 0,
                0,
                (nir - red) / (nir + red)
            )
            
            # Clip to valid NDVI range
            ndvi = np.clip(ndvi, -1, 1)
            
        return ndvi, metadata
    
    def downscale_to_satellite_resolution(
        self,
        high_res_ndvi: np.ndarray,
        src_metadata: dict,
        target_resolution: float = None
    ) -> Tuple[np.ndarray, dict]:
        """
        Downscale high-resolution drone NDVI to satellite resolution
        
        Args:
            high_res_ndvi: High-resolution NDVI array from drone
            src_metadata: Source rasterio metadata
            target_resolution: Target resolution in meters (default: self.satellite_resolution)
            
        Returns:
            downscaled_ndvi: Downscaled NDVI array
            new_metadata: Updated metadata
        """
        if target_resolution is None:
            target_resolution = self.satellite_resolution
            
        # Calculate new dimensions
        src_transform = src_metadata['transform']
        src_crs = src_metadata['crs']
        
        # Calculate scale factor
        current_resolution = abs(src_transform.a)  # pixel width
        scale_factor = current_resolution / target_resolution
        
        # Calculate new dimensions
        new_width = int(high_res_ndvi.shape[1] / scale_factor)
        new_height = int(high_res_ndvi.shape[0] / scale_factor)
        
        # Use bilinear resampling for NDVI (continuous values)
        downscaled = cv2.resize(
            high_res_ndvi,
            (new_width, new_height),
            interpolation=cv2.INTER_LINEAR
        )
        
        # Update metadata
        new_transform = rasterio.Affine(
            target_resolution, 0, src_transform.c,
            0, -target_resolution, src_transform.f
        )
        
        new_metadata = src_metadata.copy()
        new_metadata.update({
            'height': new_height,
            'width': new_width,
            'transform': new_transform,
            'count': 1
        })
        
        return downscaled, new_metadata
    
    def align_with_aoi(
        self,
        ndvi_array: np.ndarray,
        metadata: dict,
        aoi_geojson: dict
    ) -> Tuple[np.ndarray, float]:
        """
        Crop NDVI to AOI and calculate statistics
        
        Args:
            ndvi_array: NDVI array
            metadata: Rasterio metadata
            aoi_geojson: GeoJSON polygon of area of interest
            
        Returns:
            cropped_ndvi: NDVI cropped to AOI
            pixel_area: Area of each pixel in m²
        """
        # Create in-memory raster
        from rasterio.io import MemoryFile
        
        with MemoryFile() as memfile:
            with memfile.open(**metadata) as dataset:
                dataset.write(ndvi_array, 1)
                
                # Crop to AOI
                cropped, transform = mask(
                    dataset,
                    [aoi_geojson],
                    crop=True,
                    nodata=-999
                )
                
                pixel_area = abs(transform.a * transform.e)
                
        return cropped[0], pixel_area
    
    def calculate_vegetation_cover(
        self,
        ndvi: np.ndarray,
        pixel_area: float,
        threshold: float = 0.4
    ) -> Dict[str, float]:
        """
        Calculate vegetation cover statistics
        
        Args:
            ndvi: NDVI array
            pixel_area: Area of each pixel in m²
            threshold: NDVI threshold for vegetation (default: 0.4)
            
        Returns:
            Statistics dictionary with area in hectares
        """
        # Mask valid pixels
        valid_mask = ndvi != -999
        valid_ndvi = ndvi[valid_mask]
        
        # Vegetation mask
        vegetation_mask = valid_ndvi > threshold
        
        # Calculate areas
        total_pixels = valid_mask.sum()
        vegetation_pixels = vegetation_mask.sum()
        
        total_area_m2 = total_pixels * pixel_area
        vegetation_area_m2 = vegetation_pixels * pixel_area
        
        # Convert to hectares
        total_area_ha = total_area_m2 / 10000
        vegetation_area_ha = vegetation_area_m2 / 10000
        
        # Calculate percentage
        vegetation_percentage = (
            (vegetation_pixels / total_pixels * 100) if total_pixels > 0 else 0
        )
        
        return {
            'total_area_ha': round(total_area_ha, 2),
            'vegetation_area_ha': round(vegetation_area_ha, 2),
            'vegetation_percentage': round(vegetation_percentage, 2),
            'mean_ndvi': round(float(np.mean(valid_ndvi)), 3),
            'std_ndvi': round(float(np.std(valid_ndvi)), 3)
        }


def process_drone_data_for_comparison(
    drone_image_path: str,
    aoi_geojson: dict,
    red_band: int = 0,
    nir_band: int = 3
) -> Dict[str, any]:
    """
    Complete pipeline: Process drone data for satellite comparison
    
    Args:
        drone_image_path: Path to drone multispectral GeoTIFF
        aoi_geojson: GeoJSON polygon defining area of interest
        red_band: Index of red band
        nir_band: Index of NIR band
        
    Returns:
        Dictionary with processed results and statistics
    """
    processor = DroneNDVIProcessor()
    
    # Step 1: Compute high-resolution NDVI
    high_res_ndvi, metadata = processor.compute_drone_ndvi(
        drone_image_path,
        red_band_idx=red_band,
        nir_band_idx=nir_band
    )
    
    # Step 2: Downscale to satellite resolution (10m)
    downscaled_ndvi, downscaled_metadata = processor.downscale_to_satellite_resolution(
        high_res_ndvi,
        metadata
    )
    
    # Step 3: Align with AOI
    cropped_ndvi, pixel_area = processor.align_with_aoi(
        downscaled_ndvi,
        downscaled_metadata,
        aoi_geojson
    )
    
    # Step 4: Calculate statistics
    stats = processor.calculate_vegetation_cover(
        cropped_ndvi,
        pixel_area
    )
    
    return {
        'drone_stats': stats,
        'downscaled_ndvi': cropped_ndvi,
        'pixel_area_m2': pixel_area,
        'original_resolution_m': abs(metadata['transform'].a),
        'downscaled_resolution_m': 10.0
    }