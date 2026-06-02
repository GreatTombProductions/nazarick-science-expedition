#!/usr/bin/env python3
"""
STAC search — query AWS Earth Search for Sentinel-2 L2A tiles.

Primary data source for the expedition. Searches the Kem Kem Group
study area for cloud-free Sentinel-2 imagery.

Layer 4 — Domain Tools for Season 1.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Data ingestion entry point. The scout agent uses this
# to acquire new tiles for the pipeline. Verified against AWS Earth Search
# in smoke test (Momon s65).

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("nse.stac_search")

# AWS Earth Search STAC API — the primary, no-auth endpoint
EARTH_SEARCH_URL = "https://earth-search.aws.element84.com/v1"

# Default study area: Kem Kem Group region, Morocco
# bbox: [west, south, east, north]
KEM_KEM_BBOX = [-3.5, 31.5, -2.5, 32.5]

# Sentinel-2 L2A collection ID on Earth Search
COLLECTION = "sentinel-2-l2a"

# Default search parameters
DEFAULT_MAX_CLOUD = 10.0  # % cloud cover
DEFAULT_LIMIT = 50


def search(bbox: Optional[list[float]] = None,
           date_range: Optional[str] = None,
           max_cloud: float = DEFAULT_MAX_CLOUD,
           limit: int = DEFAULT_LIMIT) -> list[dict]:
    """
    Search AWS Earth Search for Sentinel-2 L2A tiles.

    Args:
        bbox: [west, south, east, north] in WGS84. Defaults to Kem Kem.
        date_range: ISO date range "YYYY-MM-DD/YYYY-MM-DD".
                    Defaults to last 30 days.
        max_cloud: Maximum cloud cover percentage.
        limit: Maximum number of results.

    Returns:
        List of tile dicts with:
            {
                "id": str,              # tile ID
                "datetime": str,        # acquisition datetime
                "cloud_cover": float,   # cloud cover %
                "bbox": list[float],    # tile bounding box
                "assets": dict,         # band hrefs
                "properties": dict,     # full STAC properties
            }
    """
    from pystac_client import Client

    if bbox is None:
        bbox = KEM_KEM_BBOX

    if date_range is None:
        now = datetime.now(timezone.utc)
        start = now.replace(day=1).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
        date_range = f"{start}/{end}"

    client = Client.open(EARTH_SEARCH_URL)

    try:
        search_result = client.search(
            collections=[COLLECTION],
            bbox=bbox,
            datetime=date_range,
            query={"eo:cloud_cover": {"lt": max_cloud}},
            max_items=limit,
            sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
        )

        items = list(search_result.items())
    except Exception as e:
        logger.error("STAC search failed: %s", e)
        return []

    tiles = []
    for item in items:
        props = item.properties or {}
        assets = {}

        # Extract band asset hrefs
        for key, asset in (item.assets or {}).items():
            assets[key] = {
                "href": asset.href,
                "type": getattr(asset, "media_type", None),
            }

        tiles.append({
            "id": item.id,
            "datetime": props.get("datetime", ""),
            "cloud_cover": props.get("eo:cloud_cover", -1),
            "bbox": list(item.bbox) if item.bbox else [],
            "assets": assets,
            "properties": props,
        })

    logger.info("STAC search: %d tiles found (bbox=%s, dates=%s, cloud<%s%%)",
                len(tiles), bbox, date_range, max_cloud)

    return tiles


def search_summary(tiles: list[dict]) -> str:
    """
    Generate a human-readable summary of search results.

    Used by the scout agent to report findings.
    """
    if not tiles:
        return "No tiles found matching search criteria."

    cloud_covers = [t["cloud_cover"] for t in tiles if t["cloud_cover"] >= 0]
    dates = [t["datetime"][:10] for t in tiles if t["datetime"]]

    lines = [
        f"Found {len(tiles)} Sentinel-2 L2A tiles.",
        f"Date range: {min(dates) if dates else '?'} to {max(dates) if dates else '?'}.",
    ]

    if cloud_covers:
        lines.append(
            f"Cloud cover: {min(cloud_covers):.1f}% – {max(cloud_covers):.1f}% "
            f"(median {sorted(cloud_covers)[len(cloud_covers)//2]:.1f}%)."
        )

    # Top 5 clearest tiles
    sorted_tiles = sorted(tiles, key=lambda t: t.get("cloud_cover", 100))
    lines.append("Clearest tiles:")
    for t in sorted_tiles[:5]:
        lines.append(
            f"  {t['id']} — {t['datetime'][:10]}, "
            f"{t['cloud_cover']:.1f}% cloud"
        )

    return "\n".join(lines)
