#!/usr/bin/env python3
"""
Deploy Smoke Test — Sentinel-2 Data Access Verification

Gates all downstream NSE phases. Verifies the full data access path:
  STAC search -> tile discovery -> COG HTTP range read -> pixel data

Run from any deployment platform before building domain tools.
Exit code 0 = all checks passed. Non-zero = blocked.
"""

import json
import sys
import time
import urllib.request

# --- Configuration ---
KEM_KEM_BBOX = [-3.5, 31.5, -2.5, 32.5]  # W, S, E, N
STAC_ENDPOINTS = {
    "aws_earth_search": "https://earth-search.aws.element84.com/v1",
    "copernicus_cdse": "https://stac.dataspace.copernicus.eu/v1",
    "ms_planetary_computer": "https://planetarycomputer.microsoft.com/api/stac/v1",
}
COLLECTION = "sentinel-2-l2a"
TIMEOUT = 30  # seconds per request


def check_stac_endpoint(name: str, url: str) -> dict:
    """Verify a STAC endpoint responds."""
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            elapsed = time.time() - t0
            return {"name": name, "status": resp.status, "elapsed_ms": int(elapsed * 1000), "ok": resp.status == 200}
    except Exception as e:
        return {"name": name, "status": str(e), "elapsed_ms": -1, "ok": False}


def search_tiles(stac_url: str) -> dict:
    """Search for Sentinel-2 L2A tiles over Kem Kem region."""
    search_url = f"{stac_url}/search"
    body = json.dumps({
        "collections": [COLLECTION],
        "bbox": KEM_KEM_BBOX,
        "datetime": "2025-01-01T00:00:00Z/2025-01-31T23:59:59Z",
        "limit": 5,
    }).encode()
    req = urllib.request.Request(
        search_url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            elapsed = time.time() - t0
            data = json.loads(resp.read())
            features = data.get("features", [])
            # Extract a COG URL from the first tile if available
            cog_url = None
            if features:
                assets = features[0].get("assets", {})
                # Try common band names: red, B04, visual
                for key in ["red", "B04", "b04", "visual"]:
                    if key in assets and "href" in assets[key]:
                        cog_url = assets[key]["href"]
                        break
                # Fallback: first asset with a .tif href
                if not cog_url:
                    for asset in assets.values():
                        href = asset.get("href", "")
                        if href.endswith(".tif") or ".tif?" in href:
                            cog_url = href
                            break
            return {
                "tile_count": len(features),
                "elapsed_ms": int(elapsed * 1000),
                "cog_url": cog_url,
                "ok": len(features) > 0,
            }
    except Exception as e:
        return {"tile_count": 0, "elapsed_ms": -1, "cog_url": None, "ok": False, "error": str(e)}


def check_cog_range_read(cog_url: str) -> dict:
    """Verify HTTP range read on a COG file (fetch first 1000 bytes, check TIFF magic)."""
    req = urllib.request.Request(cog_url, headers={"Range": "bytes=0-999"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            elapsed = time.time() - t0
            data = resp.read()
            status = resp.status
            # Check TIFF magic bytes (II for little-endian or MM for big-endian)
            is_tiff = len(data) >= 4 and (data[:2] == b"II" or data[:2] == b"MM")
            # Content-Range header tells us the full file size
            content_range = resp.headers.get("Content-Range", "")
            full_size = None
            if "/" in content_range:
                try:
                    full_size = int(content_range.split("/")[-1])
                except ValueError:
                    pass
            return {
                "status": status,
                "bytes_received": len(data),
                "is_tiff": is_tiff,
                "full_size_mb": round(full_size / 1e6, 1) if full_size else None,
                "elapsed_ms": int(elapsed * 1000),
                "ok": status in (200, 206) and is_tiff,
            }
    except Exception as e:
        return {"status": str(e), "bytes_received": 0, "is_tiff": False, "elapsed_ms": -1, "ok": False}


def main():
    print("=" * 60)
    print("NSE Deploy Smoke Test — Sentinel-2 Data Access")
    print("=" * 60)
    all_ok = True

    # 1. Check STAC endpoints
    print("\n[1/3] STAC Endpoint Availability")
    primary_url = None
    for name, url in STAC_ENDPOINTS.items():
        result = check_stac_endpoint(name, url)
        mark = "PASS" if result["ok"] else "FAIL"
        print(f"  {mark}  {name}: HTTP {result['status']} ({result['elapsed_ms']}ms)")
        if result["ok"] and primary_url is None:
            primary_url = url
        if not result["ok"] and name == "aws_earth_search":
            all_ok = False  # Primary must work

    if not primary_url:
        print("\n  FATAL: No STAC endpoint accessible. Cannot proceed.")
        sys.exit(1)

    # 2. Search for tiles
    print("\n[2/3] STAC Search — Kem Kem Region (Jan 2025)")
    search = search_tiles(primary_url)
    mark = "PASS" if search["ok"] else "FAIL"
    print(f"  {mark}  Tiles found: {search['tile_count']} ({search['elapsed_ms']}ms)")
    if not search["ok"]:
        all_ok = False
        if "error" in search:
            print(f"  Error: {search['error']}")

    # 3. COG range read
    print("\n[3/3] COG HTTP Range Read")
    if search.get("cog_url"):
        cog = check_cog_range_read(search["cog_url"])
        mark = "PASS" if cog["ok"] else "FAIL"
        size_str = f", full file: {cog['full_size_mb']}MB" if cog.get("full_size_mb") else ""
        print(f"  {mark}  HTTP {cog['status']}, {cog['bytes_received']} bytes, TIFF: {cog['is_tiff']}{size_str} ({cog['elapsed_ms']}ms)")
        if not cog["ok"]:
            all_ok = False
    else:
        print("  SKIP  No COG URL discovered from search results")
        all_ok = False

    # Summary
    print("\n" + "=" * 60)
    if all_ok:
        print("RESULT: ALL CHECKS PASSED")
        print("Data access path verified. Downstream phases unblocked.")
    else:
        print("RESULT: SOME CHECKS FAILED")
        print("Review failures above. Domain tools phase is blocked.")
    print("=" * 60)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
