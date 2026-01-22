"""
Drone-Based NDVI Computation & Downscaling
Processes high-resolution drone imagery and aligns it with satellite resolution
"""

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom
from typing import Dict, Tuple
import cv2


class DroneNDVIProcessor:
    def __init__(self, satellite_resolution: float = 10.0):
        self.satellite_resolution = satellite_resolution

    def compute_drone_ndvi(
        self,
        drone_image_path: str,
        red_band_idx: int = 0,
        nir_band_idx: int = 3
    ) -> Tuple[np.ndarray, dict]:

        with rasterio.open(drone_image_path) as src:
            if src.count <= max(red_band_idx, nir_band_idx):
                raise ValueError("Drone image does not contain required bands")

            red = src.read(red_band_idx + 1).astype("float32")
            nir = src.read(nir_band_idx + 1).astype("float32")

            ndvi = np.where(
                (nir + red) == 0,
                0,
                (nir - red) / (nir + red)
            )

            ndvi = np.clip(ndvi, -1, 1)

            metadata = src.meta.copy()
            metadata.update({
                "count": 1,
                "dtype": "float32"
            })

        return ndvi, metadata

    def downscale_to_satellite_resolution(
        self,
        high_res_ndvi: np.ndarray,
        src_metadata: dict,
        target_resolution: float = None
    ) -> Tuple[np.ndarray, dict]:

        if target_resolution is None:
            target_resolution = self.satellite_resolution

        transform = src_metadata["transform"]
        crs = src_metadata["crs"]

        if not crs or not crs.is_projected:
            raise ValueError("Drone raster must use a projected CRS")

        current_resolution = abs(transform.a)

        if current_resolution >= target_resolution:
            raise ValueError(
                f"Drone resolution ({current_resolution}m) "
                f"is coarser than target ({target_resolution}m)"
            )

        scale_factor = current_resolution / target_resolution

        new_width = int(high_res_ndvi.shape[1] / scale_factor)
        new_height = int(high_res_ndvi.shape[0] / scale_factor)

        downscaled = cv2.resize(
            high_res_ndvi,
            (new_width, new_height),
            interpolation=cv2.INTER_LINEAR
        )

        new_transform = rasterio.Affine(
            target_resolution,
            0,
            transform.c,
            0,
            -target_resolution,
            transform.f
        )

        new_metadata = src_metadata.copy()
        new_metadata.update({
            "height": new_height,
            "width": new_width,
            "transform": new_transform,
            "count": 1,
            "dtype": "float32"
        })

        return downscaled, new_metadata

    def align_with_aoi(
        self,
        ndvi_array: np.ndarray,
        metadata: dict,
        aoi_geojson: dict
    ) -> Tuple[np.ndarray, float]:

        from rasterio.io import MemoryFile

        aoi_projected = transform_geom(
            "EPSG:4326",
            metadata["crs"],
            aoi_geojson
        )

        with MemoryFile() as memfile:
            with memfile.open(**metadata) as dataset:
                dataset.write(ndvi_array, 1)

                cropped, transform = mask(
                    dataset,
                    [aoi_projected],
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

        valid_mask = ndvi != -999
        valid_ndvi = ndvi[valid_mask]

        vegetation_pixels = (valid_ndvi > threshold).sum()
        total_pixels = valid_mask.sum()

        total_area_ha = (total_pixels * pixel_area) / 10000
        vegetation_area_ha = (vegetation_pixels * pixel_area) / 10000

        return {
            "total_area_ha": round(total_area_ha, 2),
            "vegetation_area_ha": round(vegetation_area_ha, 2),
            "vegetation_percentage": round(
                (vegetation_pixels / total_pixels * 100) if total_pixels else 0, 2
            ),
            "mean_ndvi": round(float(np.mean(valid_ndvi)), 3),
            "std_ndvi": round(float(np.std(valid_ndvi)), 3)
        }


def process_drone_data_for_comparison(
    drone_image_path: str,
    aoi_geojson: dict,
    red_band: int = 0,
    nir_band: int = 3
) -> Dict[str, any]:

    processor = DroneNDVIProcessor()

    ndvi, meta = processor.compute_drone_ndvi(
        drone_image_path,
        red_band,
        nir_band
    )

    downscaled, down_meta = processor.downscale_to_satellite_resolution(
        ndvi,
        meta
    )

    cropped, pixel_area = processor.align_with_aoi(
        downscaled,
        down_meta,
        aoi_geojson
    )

    stats = processor.calculate_vegetation_cover(cropped, pixel_area)

    return {
        "drone_stats": stats,
        "original_resolution_m": abs(meta["transform"].a),
        "downscaled_resolution_m": processor.satellite_resolution
    }
