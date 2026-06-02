#!/usr/bin/env python3
"""
COG (Cloud Optimized GeoTIFF) tile reader with SCL cloud masking.

Reads Sentinel-2 L2A bands via HTTP range requests from AWS Earth Search.
Applies Scene Classification Layer (SCL) masking to exclude clouds,
shadows, and other non-surface pixels.

Layer 4 — Domain Tools for Season 1.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Foundation for all spatial analysis. spectral_indices.py
# and classifier.py both depend on this for band data access.

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger("nse.tile_reader")

# Sentinel-2 L2A band metadata
# Resolution: B2-B4,B8 = 10m; B5-B7,B8A,B11,B12 = 20m; B1,B9,B10 = 60m
BAND_INFO = {
    "B02": {"name": "Blue", "wavelength": 490, "resolution": 10},
    "B03": {"name": "Green", "wavelength": 560, "resolution": 10},
    "B04": {"name": "Red", "wavelength": 665, "resolution": 10},
    "B05": {"name": "Veg Red Edge 1", "wavelength": 705, "resolution": 20},
    "B06": {"name": "Veg Red Edge 2", "wavelength": 740, "resolution": 20},
    "B07": {"name": "Veg Red Edge 3", "wavelength": 783, "resolution": 20},
    "B08": {"name": "NIR", "wavelength": 842, "resolution": 10},
    "B8A": {"name": "NIR Narrow", "wavelength": 865, "resolution": 20},
    "B11": {"name": "SWIR 1", "wavelength": 1610, "resolution": 20},
    "B12": {"name": "SWIR 2", "wavelength": 2190, "resolution": 20},
}

# SCL classes to mask (not surface)
# 0=No data, 1=Saturated, 2=Dark/Shadow, 3=Cloud shadow,
# 6=Water, 8=Cloud medium, 9=Cloud high, 10=Cirrus, 11=Snow
SCL_MASK_CLASSES = {0, 1, 2, 3, 6, 8, 9, 10, 11}

# SCL classes considered valid surface
# 4=Vegetation, 5=Bare soil, 7=Unclassified (often valid in arid terrain)
SCL_SURFACE_CLASSES = {4, 5, 7}


def read_band(href: str, window: Optional[tuple] = None) -> np.ndarray:
    """
    Read a single band from a COG URL via HTTP range request.

    Args:
        href: URL to the COG file (from STAC item asset)
        window: Optional (row_off, col_off, height, width) for subset read.
                None reads the full tile.

    Returns:
        2D numpy array of reflectance values (uint16).
    """
    import rasterio
    from rasterio.windows import Window

    with rasterio.open(href) as src:
        if window:
            row_off, col_off, height, width = window
            w = Window(col_off, row_off, width, height)
            data = src.read(1, window=w)
        else:
            data = src.read(1)

    return data


def read_bands(assets: dict, band_names: list[str],
               window: Optional[tuple] = None) -> dict[str, np.ndarray]:
    """
    Read multiple bands from STAC item assets.

    Args:
        assets: Dict mapping band names to asset dicts with 'href' keys.
                From a pystac Item's assets property.
        band_names: List of band names to read (e.g., ["B04", "B03", "B11"]).
        window: Optional spatial subset window.

    Returns:
        Dict mapping band names to 2D numpy arrays.
    """
    bands = {}
    for name in band_names:
        asset = assets.get(name) or assets.get(name.lower())
        if asset is None:
            logger.warning("Band %s not found in assets", name)
            continue

        href = asset if isinstance(asset, str) else asset.get("href", "")
        if not href:
            logger.warning("No href for band %s", name)
            continue

        try:
            bands[name] = read_band(href, window)
        except Exception as e:
            logger.error("Failed to read band %s from %s: %s", name, href, e)

    return bands


def read_scl(assets: dict, window: Optional[tuple] = None) -> Optional[np.ndarray]:
    """
    Read the Scene Classification Layer (SCL) band.

    Args:
        assets: STAC item assets dict.
        window: Optional spatial subset.

    Returns:
        2D numpy array of SCL class values, or None if unavailable.
    """
    scl_asset = assets.get("SCL") or assets.get("scl")
    if scl_asset is None:
        return None

    href = scl_asset if isinstance(scl_asset, str) else scl_asset.get("href", "")
    if not href:
        return None

    try:
        return read_band(href, window)
    except Exception as e:
        logger.error("Failed to read SCL: %s", e)
        return None


def apply_cloud_mask(band_data: np.ndarray, scl: np.ndarray,
                     mask_classes: Optional[set] = None) -> np.ndarray:
    """
    Apply SCL-based cloud mask to a band array.

    Pixels matching mask_classes are set to NaN (for float) or 0 (for int).
    If SCL resolution differs from band resolution, SCL is resampled.

    Args:
        band_data: 2D array of band values.
        scl: 2D array of SCL class values.
        mask_classes: Set of SCL classes to mask. Defaults to SCL_MASK_CLASSES.

    Returns:
        Masked band array (float32 with NaN for masked pixels).
    """
    if mask_classes is None:
        mask_classes = SCL_MASK_CLASSES

    # Resample SCL if resolution differs (SCL is 20m, some bands are 10m)
    if scl.shape != band_data.shape:
        from scipy.ndimage import zoom
        factors = (
            band_data.shape[0] / scl.shape[0],
            band_data.shape[1] / scl.shape[1],
        )
        scl = zoom(scl, factors, order=0)  # Nearest-neighbor for classification

    # Build mask: True where pixel should be masked
    mask = np.isin(scl, list(mask_classes))

    # Convert to float and apply mask
    result = band_data.astype(np.float32)
    result[mask] = np.nan

    return result


def surface_fraction(scl: np.ndarray) -> float:
    """
    Calculate the fraction of pixels classified as surface.

    Useful for quality assessment — tiles with <50% surface pixels
    are likely too contaminated for reliable analysis.

    Args:
        scl: 2D SCL array.

    Returns:
        Fraction [0.0, 1.0] of pixels in SCL_SURFACE_CLASSES.
    """
    total = scl.size
    if total == 0:
        return 0.0
    surface = np.isin(scl, list(SCL_SURFACE_CLASSES)).sum()
    return float(surface / total)
