#!/usr/bin/env python3
"""
Territory tracker management — tile lifecycle and spatial state.

Manages the territory_tracker.json state file: adding tiles from STAC search,
updating tile status through the pipeline, computing statistics, and querying
for pending/active/flagged tiles.

Layer 2 — State Management Infrastructure.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Core state management for tile lifecycle. Every pipeline
# stage reads territory status; acquire/analyze/validate stages write to it.

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from checkpoint import CheckpointManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
TERRITORY_PATH = STATE_DIR / "territory_tracker.json"

# Valid tile status transitions
TILE_STATUSES = ["pending", "active", "analyzed", "validated", "complete", "flagged", "error"]
VALID_TRANSITIONS = {
    "pending": ["active", "flagged"],
    "active": ["analyzed", "error", "flagged"],
    "analyzed": ["validated", "flagged"],
    "validated": ["complete", "flagged"],
    "flagged": ["pending", "active"],  # Can be returned to pipeline
    "error": ["pending"],              # Retry from beginning
}


class TerritoryManager:
    """
    Manages the spatial state of the expedition.

    Tile lifecycle:
        pending → active → analyzed → validated → complete
                                      ↗ flagged (any stage)
                                      ↗ error (from active)
    """

    def __init__(self, checkpoint_mgr: Optional[CheckpointManager] = None):
        self.checkpoint = checkpoint_mgr or CheckpointManager(STATE_DIR)
        self._load()

    def _load(self) -> None:
        """Load territory tracker from disk."""
        if TERRITORY_PATH.exists():
            self.data = json.loads(TERRITORY_PATH.read_text())
        else:
            self.data = {
                "version": 1,
                "season": "kem-kem-s1",
                "bbox": [-3.5, 31.5, -2.5, 32.5],
                "updated": None,
                "tiles": {},
                "statistics": self._empty_stats(),
            }
            self._save()

    def _save(self) -> None:
        """Persist territory state atomically."""
        self.data["updated"] = _now_iso()
        self._recompute_stats()
        self.checkpoint.write_atomic(
            TERRITORY_PATH,
            json.dumps(self.data, indent=2, default=str),
        )

    def _empty_stats(self) -> dict:
        return {"total_tiles": 0, "pending": 0, "active": 0,
                "analyzed": 0, "validated": 0, "complete": 0,
                "flagged": 0, "error": 0}

    def _recompute_stats(self) -> None:
        """Recompute statistics from tile data."""
        stats = self._empty_stats()
        for tile in self.data["tiles"].values():
            status = tile.get("status", "pending")
            stats["total_tiles"] += 1
            if status in stats:
                stats[status] += 1
        self.data["statistics"] = stats

    # -------------------------------------------------------------------
    # Tile operations
    # -------------------------------------------------------------------

    def add_tile(self, tile_id: str, metadata: dict) -> dict:
        """
        Add a new tile from STAC search results.

        Args:
            tile_id: Sentinel-2 tile identifier (e.g., "T29RNQ_20250115")
            metadata: STAC metadata dict with at minimum:
                - datetime: acquisition datetime
                - cloud_cover: percentage
                - bbox: tile bounding box [optional, from STAC item]

        Returns:
            The created tile record.
        """
        if tile_id in self.data["tiles"]:
            return self.data["tiles"][tile_id]

        tile = {
            "id": tile_id,
            "status": "pending",
            "added": _now_iso(),
            "updated": _now_iso(),
            "metadata": {
                "datetime": metadata.get("datetime"),
                "cloud_cover": metadata.get("cloud_cover"),
                "bbox": metadata.get("bbox"),
            },
            "findings": [],
            "classification": None,
            "confidence": None,
            "history": [
                {"status": "pending", "timestamp": _now_iso(), "agent": "scout"},
            ],
        }
        self.data["tiles"][tile_id] = tile
        self._save()
        return tile

    def add_tiles_batch(self, tiles: list[dict]) -> int:
        """
        Add multiple tiles from STAC search. Returns count of newly added.

        Each dict in tiles must have 'id' and metadata fields.
        """
        added = 0
        for t in tiles:
            tile_id = t.get("id", "")
            if tile_id and tile_id not in self.data["tiles"]:
                self.add_tile(tile_id, t)
                added += 1
        return added

    def update_status(self, tile_id: str, new_status: str,
                      agent: str = "harness", note: str = "") -> bool:
        """
        Transition a tile to a new status.

        Validates the transition is legal. Returns True if updated.
        """
        if tile_id not in self.data["tiles"]:
            return False

        tile = self.data["tiles"][tile_id]
        current = tile["status"]

        if new_status not in VALID_TRANSITIONS.get(current, []):
            return False

        tile["status"] = new_status
        tile["updated"] = _now_iso()
        tile["history"].append({
            "status": new_status,
            "timestamp": _now_iso(),
            "agent": agent,
            "note": note,
        })
        self._save()
        return True

    def add_finding(self, tile_id: str, finding: dict) -> bool:
        """
        Attach a finding to a tile.

        Finding dict should include: claim, evidence, confidence, agent.
        """
        if tile_id not in self.data["tiles"]:
            return False

        tile = self.data["tiles"][tile_id]
        finding["timestamp"] = _now_iso()
        tile["findings"].append(finding)
        tile["updated"] = _now_iso()
        self._save()
        return True

    def set_classification(self, tile_id: str, classification: str,
                           confidence: float) -> bool:
        """Set the classification result for a tile."""
        if tile_id not in self.data["tiles"]:
            return False

        tile = self.data["tiles"][tile_id]
        tile["classification"] = classification
        tile["confidence"] = confidence
        tile["updated"] = _now_iso()
        self._save()
        return True

    # -------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------

    def get_tile(self, tile_id: str) -> Optional[dict]:
        """Get a single tile record."""
        return self.data["tiles"].get(tile_id)

    def get_pending(self, limit: int = 10) -> list[dict]:
        """Get pending tiles, oldest first."""
        pending = [t for t in self.data["tiles"].values()
                   if t["status"] == "pending"]
        pending.sort(key=lambda t: t.get("added", ""))
        return pending[:limit]

    def get_by_status(self, status: str, limit: int = 50) -> list[dict]:
        """Get tiles by status."""
        return [t for t in self.data["tiles"].values()
                if t["status"] == status][:limit]

    def get_flagged(self) -> list[dict]:
        """Get all flagged tiles for review."""
        return [t for t in self.data["tiles"].values()
                if t["status"] == "flagged"]

    def get_recent_findings(self, n: int = 10) -> list[dict]:
        """Get the N most recent findings across all tiles."""
        all_findings = []
        for tile in self.data["tiles"].values():
            for f in tile.get("findings", []):
                f_copy = dict(f)
                f_copy["tile_id"] = tile["id"]
                all_findings.append(f_copy)
        all_findings.sort(key=lambda f: f.get("timestamp", ""), reverse=True)
        return all_findings[:n]

    def statistics(self) -> dict:
        """Return current territory statistics."""
        self._recompute_stats()
        return dict(self.data["statistics"])

    def summary_for_briefing(self) -> str:
        """
        Generate a compact territory summary for agent briefing injection.

        Designed to be token-efficient for DSV4-Flash context budget.
        """
        stats = self.statistics()
        total = stats["total_tiles"]
        if total == 0:
            return "Territory: No tiles acquired yet."

        parts = [f"Territory: {total} tiles total"]
        for status in ["pending", "active", "analyzed", "validated",
                       "complete", "flagged", "error"]:
            count = stats.get(status, 0)
            if count > 0:
                parts.append(f"{count} {status}")

        return " | ".join(parts) + "."


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
