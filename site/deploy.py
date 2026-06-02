#!/usr/bin/env python3
"""
NSE Static Site Deploy Script

Reads findings from the expedition's state store, generates sharded
static JSON indexes, and deploys to GitHub Pages.

Same pattern as 30 quest board tools — letter-sharded search index
+ MD5-keyed detail shards. Adapted for the finding manifest schema.

Usage:
  python3 deploy.py                     # Build site data only
  python3 deploy.py --push              # Build and push to GitHub Pages
  python3 deploy.py --push --incremental  # Only update new findings
"""

import hashlib
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# --- Configuration ---

SITE_DIR = Path(__file__).parent
PROJECT_DIR = SITE_DIR.parent
STATE_DIR = PROJECT_DIR / "state"
FINDINGS_DATA_DIR = SITE_DIR / "findings" / "data"
FINDINGS_DETAIL_DIR = SITE_DIR / "findings" / "detail"
LOG_DATA_DIR = SITE_DIR / "log" / "data"
TOOL_REGISTRY_FILE = PROJECT_DIR / "tools" / "tool_registry.json"

GITHUB_REPO = "git@github.com:GreatTombProductions/nazarick-science-expedition.git"
DEPLOY_BRANCH = "gh-pages"

N_DETAIL_SHARDS = 256
MAX_LATEST_FINDINGS = 6


def load_findings() -> list[dict]:
    """Load validated findings from state store."""
    findings_dir = STATE_DIR / "findings"
    if not findings_dir.exists():
        return []

    findings = []
    for f in sorted(findings_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            findings.append(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  WARN: Skipping {f.name}: {e}", file=sys.stderr)
    return findings


def load_journal() -> list[dict]:
    """Load expedition journal for log generation."""
    journal_file = STATE_DIR / "journal.jsonl"
    if not journal_file.exists():
        return []

    entries = []
    for line in journal_file.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def build_index_shards(findings: list[dict]) -> dict[str, list]:
    """Letter-shard findings by claim text first character."""
    shards = defaultdict(list)
    for f in findings:
        claim = f.get("claim", "")
        key = claim[0].lower() if claim else "_"
        key = key if key.isalpha() else "_"
        shards[key].append({
            "id": f["id"],
            "claim": f["claim"],
            "date": f.get("date", ""),
            "confidence": f.get("confidence", 0),
            "domain": f.get("domain", ""),
            "season": f.get("season", 1),
            "method": f.get("method", ""),
            "tier": f.get("validation", {}).get("status", "preliminary").upper(),
            "tile_id": f.get("location", {}).get("tile_id", ""),
        })
    return dict(shards)


def build_detail_shards(findings: list[dict]) -> dict[str, list]:
    """MD5-key findings into 256 detail shards."""
    shards = defaultdict(list)
    for f in findings:
        shard_key = hashlib.md5(f["id"].encode()).hexdigest()[:2]
        shards[shard_key].append(f)
    return dict(shards)


def build_manifest(findings: list[dict]) -> dict:
    """Build the findings manifest with summary stats."""
    if not findings:
        return {
            "total": 0,
            "tiles_surveyed": 0,
            "validated": 0,
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "domains": [],
            "seasons": [],
            "latest": [],
        }

    validated = [f for f in findings if f.get("validation", {}).get("status") == "validated"]
    tiles = set()
    for f in findings:
        tid = f.get("location", {}).get("tile_id")
        if tid:
            tiles.add(tid)

    # Latest findings for landing page
    sorted_findings = sorted(findings, key=lambda f: f.get("date", ""), reverse=True)
    latest = []
    for f in sorted_findings[:MAX_LATEST_FINDINGS]:
        latest.append({
            "id": f["id"],
            "claim": f["claim"],
            "date": f.get("date", ""),
            "confidence": f.get("confidence", 0),
            "method": f.get("method", ""),
            "tier": f.get("validation", {}).get("status", "preliminary").upper(),
            "tile_id": f.get("location", {}).get("tile_id", ""),
        })

    return {
        "total": len(findings),
        "tiles_surveyed": len(tiles),
        "validated": len(validated),
        "last_updated": max(f.get("date", "") for f in findings) or datetime.now().strftime("%Y-%m-%d"),
        "domains": sorted(set(f.get("domain", "") for f in findings if f.get("domain"))),
        "seasons": sorted(set(f.get("season", 1) for f in findings)),
        "latest": latest,
    }


def write_json(path: Path, data):
    """Write JSON with directory creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))


def build_site_data(findings: list[dict]):
    """Generate all static JSON data files."""
    print(f"\n  Findings: {len(findings)}")

    # Index shards
    index_shards = build_index_shards(findings)
    FINDINGS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for key, data in index_shards.items():
        write_json(FINDINGS_DATA_DIR / f"index_{key}.json", data)
    print(f"  Index shards: {len(index_shards)}")

    # Detail shards
    detail_shards = build_detail_shards(findings)
    FINDINGS_DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    for key, data in detail_shards.items():
        write_json(FINDINGS_DETAIL_DIR / f"{key}.json", data)
    print(f"  Detail shards: {len(detail_shards)}")

    # Manifest
    manifest = build_manifest(findings)
    write_json(FINDINGS_DATA_DIR / "findings-manifest.json", manifest)
    print(f"  Manifest: {manifest['total']} findings, {manifest['validated']} validated, {manifest['tiles_surveyed']} tiles")


def push_to_github():
    """Push site to GitHub Pages."""
    print("\n  Pushing to GitHub Pages...")

    # Create a temporary directory for the deploy
    deploy_dir = SITE_DIR / ".deploy"
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)

    # Clone the gh-pages branch (or create it)
    result = subprocess.run(
        ["git", "clone", "--branch", DEPLOY_BRANCH, "--depth", "1", GITHUB_REPO, str(deploy_dir)],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        # Branch doesn't exist yet — create it
        deploy_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init"], cwd=deploy_dir, capture_output=True)
        subprocess.run(["git", "checkout", "-b", DEPLOY_BRANCH], cwd=deploy_dir, capture_output=True)

    # Copy site files
    for item in SITE_DIR.iterdir():
        if item.name.startswith(".") or item.name == "deploy.py":
            continue
        dest = deploy_dir / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    # Add .nojekyll for GitHub Pages
    (deploy_dir / ".nojekyll").touch()

    # Commit and push
    subprocess.run(["git", "add", "-A"], cwd=deploy_dir, capture_output=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    result = subprocess.run(
        ["git", "commit", "-m", f"deploy: {timestamp}"],
        cwd=deploy_dir, capture_output=True, text=True,
    )

    if "nothing to commit" in result.stdout:
        print("  No changes to deploy.")
    else:
        result = subprocess.run(
            ["git", "push", "origin", DEPLOY_BRANCH],
            cwd=deploy_dir, capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("  Deployed successfully.")
        else:
            print(f"  Push failed: {result.stderr}", file=sys.stderr)

    # Cleanup
    shutil.rmtree(deploy_dir, ignore_errors=True)


def main():
    push = "--push" in sys.argv

    print("=" * 50)
    print("NSE Static Site Deploy")
    print("=" * 50)

    # Load data
    findings = load_findings()

    # Build site data
    build_site_data(findings)

    # Calculate total site size
    total_size = 0
    for f in SITE_DIR.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            total_size += f.stat().st_size
    print(f"\n  Total site size: {total_size / 1024:.1f} KB")

    if push:
        push_to_github()
    else:
        print("\n  Run with --push to deploy to GitHub Pages.")

    print("\n" + "=" * 50)
    print("Done.")
    print("=" * 50)


if __name__ == "__main__":
    main()
