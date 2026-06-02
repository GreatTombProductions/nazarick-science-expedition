#!/usr/bin/env python3
"""
Journal management — append-only research history with query interface.

The journal (state/journal.jsonl) is the append-only record of every agent
turn. This module provides query/filter/aggregation over that record for
briefing assembly and synthesis stages.

Layer 2 — State Management Infrastructure.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Read-only query layer over the journal. The orchestrator
# appends entries; this module reads and aggregates them.

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
JOURNAL_PATH = STATE_DIR / "journal.jsonl"


class JournalManager:
    """
    Query interface over the expedition journal.

    The journal is append-only JSONL written by the orchestrator.
    Each entry has: task_id, stage, agent, success, findings_count, timestamp.
    """

    def __init__(self, journal_path: Path = JOURNAL_PATH):
        self.path = journal_path

    def _read_entries(self) -> list[dict]:
        """Read all journal entries."""
        if not self.path.exists():
            return []
        entries = []
        for line in self.path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries

    # -------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------

    def recent(self, n: int = 10) -> list[dict]:
        """Get the N most recent journal entries."""
        entries = self._read_entries()
        return entries[-n:]

    def by_agent(self, agent: str, limit: int = 50) -> list[dict]:
        """Get entries for a specific agent."""
        entries = self._read_entries()
        filtered = [e for e in entries if e.get("agent") == agent]
        return filtered[-limit:]

    def by_stage(self, stage: str, limit: int = 50) -> list[dict]:
        """Get entries for a specific stage."""
        entries = self._read_entries()
        filtered = [e for e in entries if e.get("stage") == stage]
        return filtered[-limit:]

    def since(self, hours: float = 24) -> list[dict]:
        """Get entries from the last N hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()
        entries = self._read_entries()
        return [e for e in entries
                if e.get("timestamp", "") >= cutoff_iso]

    def failures(self, limit: int = 20) -> list[dict]:
        """Get recent failed entries."""
        entries = self._read_entries()
        failed = [e for e in entries if not e.get("success", True)]
        return failed[-limit:]

    def with_findings(self, limit: int = 20) -> list[dict]:
        """Get entries that produced findings."""
        entries = self._read_entries()
        has_findings = [e for e in entries
                        if e.get("findings_count", 0) > 0]
        return has_findings[-limit:]

    # -------------------------------------------------------------------
    # Aggregation
    # -------------------------------------------------------------------

    def agent_stats(self) -> dict:
        """Per-agent statistics: total turns, successes, findings."""
        entries = self._read_entries()
        stats = {}
        for e in entries:
            agent = e.get("agent", "unknown")
            if agent not in stats:
                stats[agent] = {"turns": 0, "successes": 0,
                                "failures": 0, "findings": 0}
            stats[agent]["turns"] += 1
            if e.get("success", True):
                stats[agent]["successes"] += 1
            else:
                stats[agent]["failures"] += 1
            stats[agent]["findings"] += e.get("findings_count", 0)
        return stats

    def stage_stats(self) -> dict:
        """Per-stage statistics."""
        entries = self._read_entries()
        stats = {}
        for e in entries:
            stage = e.get("stage", "unknown")
            if stage not in stats:
                stats[stage] = {"turns": 0, "successes": 0, "findings": 0}
            stats[stage]["turns"] += 1
            if e.get("success", True):
                stats[stage]["successes"] += 1
            stats[stage]["findings"] += e.get("findings_count", 0)
        return stats

    def total_entries(self) -> int:
        """Total number of journal entries."""
        return len(self._read_entries())

    # -------------------------------------------------------------------
    # Briefing support
    # -------------------------------------------------------------------

    def summary_for_briefing(self, hours: float = 168) -> str:
        """
        Compact summary for agent briefing injection.

        Default window: 7 days (168 hours). Token-efficient.
        """
        recent = self.since(hours)
        if not recent:
            return "Journal: No activity recorded yet."

        total = len(recent)
        successes = sum(1 for e in recent if e.get("success", True))
        findings = sum(e.get("findings_count", 0) for e in recent)

        # Stage breakdown
        stages = {}
        for e in recent:
            s = e.get("stage", "?")
            stages[s] = stages.get(s, 0) + 1

        stage_str = ", ".join(f"{s}:{c}" for s, c in sorted(stages.items()))

        return (
            f"Journal ({total} entries, last {int(hours)}h): "
            f"{successes} succeeded, {total - successes} failed, "
            f"{findings} findings. Stages: {stage_str}."
        )

    def last_agent_entry(self, agent: str) -> Optional[dict]:
        """Get the most recent entry for a specific agent."""
        entries = self.by_agent(agent, limit=1)
        return entries[-1] if entries else None
