#!/usr/bin/env python3
"""
Spectral indices for Kem Kem Group lithological analysis.

Computes band ratio indices from Sentinel-2 data for geological
classification. Targets: iron oxide (Fe3+), carbonate, clay minerals,
vegetation (NDVI), and PCA on SWIR bands.

All computations are pure numpy — no external ML dependencies.

Layer 4 — Domain Tools for Season 1.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: The geological analysis core. These indices are the
# features fed to classifier.py. Index selection from intelligence brief
# Section I (Kem Kem spectral targets) and analogous Moroccan studies.

import logging

import numpy as np

logger = logging.getLogger("nse.spectral_indices")

# Sentinel-2 band scaling: DN to reflectance
# L2A products store reflectance * 10000 as uint16
SCALE_FACTOR = 10000.0


def _safe_ratio(numerator: np.ndarray, denominator: np.ndarray,
                fill: float = np.nan) -> np.ndarray:
    """
    Compute ratio with divide-by-zero protection.

    Returns float32 array with fill value where denominator is zero or NaN.
    """
    num = numerator.astype(np.float32) / SCALE_FACTOR
    den = denominator.astype(np.float32) / SCALE_FACTOR

    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(den != 0, num / den, fill)

    # Propagate NaN from masked pixels
    result = np.where(np.isnan(num) | np.isnan(den), np.nan, result)
    return result


# ---------------------------------------------------------------------------
# Individual indices
# ---------------------------------------------------------------------------

def iron_oxide(b04: np.ndarray, b03: np.ndarray) -> np.ndarray:
    """
    Iron oxide (Fe3+) index — B4/B3 (Red/Green ratio).

    Primary target: ferruginous sandstones of the Gara Sbaa Formation.
    Values > 1.2 typically indicate iron-rich surfaces in arid terrain.

    Args:
        b04: Red band (665nm)
        b03: Green band (560nm)

    Returns:
        2D float32 array. Higher values = more iron oxide absorption.
    """
    return _safe_ratio(b04, b03)


def carbonate(b11: np.ndarray, b02: np.ndarray) -> np.ndarray:
    """
    Carbonate index — B11/B2 (SWIR1/Blue ratio).

    Primary boundary marker: Cenomanian-Turonian limestone cap.
    Carbonates have distinctive SWIR absorption features.

    Args:
        b11: SWIR1 band (1610nm)
        b02: Blue band (490nm)

    Returns:
        2D float32 array. Higher values = carbonate absorption.
    """
    return _safe_ratio(b11, b02)


def clay_swir(b11: np.ndarray, b12: np.ndarray) -> np.ndarray:
    """
    Clay mineral index — B11/B12 (SWIR1/SWIR2 ratio).

    Targets mudstone horizons. Clay minerals (kaolinite, illite,
    montmorillonite) show absorption at ~2.2μm (B12).

    Args:
        b11: SWIR1 band (1610nm)
        b12: SWIR2 band (2190nm)

    Returns:
        2D float32 array. Higher values = more clay content.
    """
    return _safe_ratio(b11, b12)


def clay_vre(b11: np.ndarray, b05: np.ndarray) -> np.ndarray:
    """
    Alternative clay index — B11/B5 (SWIR1/Veg Red Edge ratio).

    Complementary to clay_swir; different sensitivity profile for
    distinguishing clay assemblages.

    Args:
        b11: SWIR1 band (1610nm)
        b05: Vegetation Red Edge 1 band (705nm)

    Returns:
        2D float32 array.
    """
    return _safe_ratio(b11, b05)


def ndvi(b08: np.ndarray, b04: np.ndarray) -> np.ndarray:
    """
    Normalized Difference Vegetation Index.

    NDVI = (NIR - Red) / (NIR + Red)

    Used to mask vegetation from geological analysis. In the Kem Kem
    arid region, NDVI > 0.2 typically indicates irrigated agriculture
    or riparian vegetation (not geological surface).

    Args:
        b08: NIR band (842nm)
        b04: Red band (665nm)

    Returns:
        2D float32 array in [-1, 1]. Values > 0.2 suggest vegetation.
    """
    nir = b08.astype(np.float32) / SCALE_FACTOR
    red = b04.astype(np.float32) / SCALE_FACTOR

    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(
            (nir + red) != 0,
            (nir - red) / (nir + red),
            np.nan,
        )

    result = np.where(np.isnan(nir) | np.isnan(red), np.nan, result)
    return result


# ---------------------------------------------------------------------------
# PCA on SWIR bands
# ---------------------------------------------------------------------------

def swir_pca(b11: np.ndarray, b12: np.ndarray,
             n_components: int = 2) -> dict:
    """
    PCA on SWIR bands to separate clay vs. carbonate assemblages.

    Projects B11 and B12 into principal components. PC1 typically
    captures overall SWIR brightness; PC2 captures the clay-carbonate
    contrast.

    Args:
        b11: SWIR1 band (1610nm)
        b12: SWIR2 band (2190nm)
        n_components: Number of PCs to retain (max 2 for 2 bands).

    Returns:
        {
            "components": list[np.ndarray],  # PC images
            "explained_variance": list[float],  # variance ratios
            "mean": np.ndarray,  # band means (for inverse transform)
        }
    """
    s11 = b11.astype(np.float32) / SCALE_FACTOR
    s12 = b12.astype(np.float32) / SCALE_FACTOR

    # Flatten spatial dimensions, exclude NaN pixels
    h, w = s11.shape
    flat = np.stack([s11.ravel(), s12.ravel()], axis=1)

    valid = ~np.any(np.isnan(flat), axis=1)
    if valid.sum() < 10:
        logger.warning("Too few valid pixels for PCA (%d)", valid.sum())
        return {
            "components": [np.full((h, w), np.nan)] * n_components,
            "explained_variance": [0.0] * n_components,
            "mean": np.array([0.0, 0.0]),
        }

    valid_data = flat[valid]

    # Center
    mean = valid_data.mean(axis=0)
    centered = valid_data - mean

    # SVD-based PCA (works for 2 bands without sklearn)
    _, s_vals, vt = np.linalg.svd(centered, full_matrices=False)
    variance = (s_vals ** 2) / (len(centered) - 1)
    total_var = variance.sum()
    explained = (variance / total_var).tolist() if total_var > 0 else [0.0, 0.0]

    # Project all pixels (including NaN → NaN)
    components = []
    for i in range(min(n_components, 2)):
        pc = np.full(h * w, np.nan)
        projected = centered @ vt[i]
        pc[valid] = projected
        components.append(pc.reshape(h, w))

    return {
        "components": components,
        "explained_variance": explained[:n_components],
        "mean": mean,
    }


# ---------------------------------------------------------------------------
# Composite computation
# ---------------------------------------------------------------------------

def compute_all(bands: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """
    Compute all available spectral indices from provided bands.

    Args:
        bands: Dict mapping band names (e.g., "B04") to 2D arrays.

    Returns:
        Dict mapping index names to 2D float32 arrays.
        Only indices with all required bands present are computed.
    """
    indices = {}

    if "B04" in bands and "B03" in bands:
        indices["iron_oxide"] = iron_oxide(bands["B04"], bands["B03"])

    if "B11" in bands and "B02" in bands:
        indices["carbonate"] = carbonate(bands["B11"], bands["B02"])

    if "B11" in bands and "B12" in bands:
        indices["clay_swir"] = clay_swir(bands["B11"], bands["B12"])

    if "B11" in bands and "B05" in bands:
        indices["clay_vre"] = clay_vre(bands["B11"], bands["B05"])

    if "B08" in bands and "B04" in bands:
        indices["ndvi"] = ndvi(bands["B08"], bands["B04"])

    if "B11" in bands and "B12" in bands:
        pca = swir_pca(bands["B11"], bands["B12"])
        for i, pc in enumerate(pca["components"]):
            indices[f"swir_pc{i+1}"] = pc

    return indices


def index_statistics(index_data: np.ndarray, name: str = "") -> dict:
    """
    Compute summary statistics for a spectral index.

    Ignores NaN pixels (masked/cloud). Useful for briefing assembly.
    """
    valid = index_data[~np.isnan(index_data)]
    if valid.size == 0:
        return {"name": name, "valid_pixels": 0}

    return {
        "name": name,
        "valid_pixels": int(valid.size),
        "mean": float(np.mean(valid)),
        "std": float(np.std(valid)),
        "min": float(np.min(valid)),
        "max": float(np.max(valid)),
        "p25": float(np.percentile(valid, 25)),
        "p50": float(np.percentile(valid, 50)),
        "p75": float(np.percentile(valid, 75)),
    }
