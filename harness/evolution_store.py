#!/usr/bin/env python3
"""
Evolution store — cross-run learning with temporal decay.

Captures lessons that accumulate across expedition runs: what worked,
what failed, what to try differently. Implements:
  - 30-day half-life for relevance decay
  - 1.5x severity weighting (failures teach more than successes)
  - 2x stage-match boost (lessons from matching stages are more relevant)

PaperOrchestra steal: structured worklogs as institutional memory.
AI Scientist steal: idea archive with reflection.

Layer 2 — State Management Infrastructure.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: The expedition's institutional memory. Every synthesis
# stage reads this; validation and analysis stages contribute to it.
# Novel contribution: no surveyed framework implements knowledge accumulation
# with staleness detection (autoresearch-teardown.md Section 4).

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from checkpoint import CheckpointManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
EVOLUTION_PATH = STATE_DIR / "evolution_store.jsonl"

# Decay parameters
HALF_LIFE_DAYS = 30        # Relevance halves every 30 days
SEVERITY_WEIGHT = 1.5      # Failures weighted 1.5x over successes
STAGE_MATCH_BOOST = 2.0    # Lessons from matching stages weighted 2x


class EvolutionStore:
    """
    Cross-run learning store for the expedition.

    Each lesson is a structured record:
        {
            "id": str,              # unique identifier
            "timestamp": str,       # when learned
            "stage": str,           # which pipeline stage
            "agent": str,           # which agent learned it
            "type": str,            # "success" | "failure" | "observation"
            "lesson": str,          # what was learned
            "context": str,         # circumstances
            "severity": float,      # 0.0–1.0 impact severity
            "applied_count": int,   # times this lesson was surfaced
            "last_applied": str,    # last time surfaced in a briefing
        }
    """

    def __init__(self, checkpoint_mgr: Optional[CheckpointManager] = None):
        self.checkpoint = checkpoint_mgr or CheckpointManager(STATE_DIR)
        self.path = EVOLUTION_PATH

    def _read_lessons(self) -> list[dict]:
        """Read all lessons from the store."""
        if not self.path.exists():
            return []
        lessons = []
        for line in self.path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    lessons.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return lessons

    def _append(self, lesson: dict) -> None:
        """Append a lesson to the store."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a") as f:
            f.write(json.dumps(lesson, default=str) + "\n")

    # -------------------------------------------------------------------
    # Write operations
    # -------------------------------------------------------------------

    def record_lesson(self, stage: str, agent: str, lesson_type: str,
                      lesson: str, context: str = "",
                      severity: float = 0.5) -> dict:
        """
        Record a new lesson learned during expedition operations.

        Args:
            stage: Pipeline stage where the lesson was learned
            agent: Agent that learned the lesson
            lesson_type: "success", "failure", or "observation"
            lesson: What was learned (concise statement)
            context: Circumstances (tile, finding, tool, etc.)
            severity: Impact severity 0.0–1.0

        Returns:
            The created lesson record.
        """
        now = _now_iso()
        record = {
            "id": f"evo-{stage}-{int(datetime.now(timezone.utc).timestamp())}",
            "timestamp": now,
            "stage": stage,
            "agent": agent,
            "type": lesson_type,
            "lesson": lesson,
            "context": context,
            "severity": max(0.0, min(1.0, severity)),
            "applied_count": 0,
            "last_applied": None,
        }
        self._append(record)
        return record

    # -------------------------------------------------------------------
    # Query with relevance scoring
    # -------------------------------------------------------------------

    def query(self, current_stage: str = "", limit: int = 5) -> list[dict]:
        """
        Get the most relevant lessons for the current context.

        Relevance = temporal_decay × severity_weight × stage_match_boost.

        Args:
            current_stage: Current pipeline stage (for stage-match boost)
            limit: Maximum lessons to return

        Returns:
            List of lessons with 'relevance_score' field added, sorted
            by relevance descending.
        """
        lessons = self._read_lessons()
        now = datetime.now(timezone.utc)

        scored = []
        for lesson in lessons:
            # Temporal decay: half-life of 30 days
            ts = lesson.get("timestamp", "")
            try:
                lesson_time = datetime.fromisoformat(ts)
                if lesson_time.tzinfo is None:
                    lesson_time = lesson_time.replace(tzinfo=timezone.utc)
                age_days = (now - lesson_time).total_seconds() / 86400
            except (ValueError, TypeError):
                age_days = 365  # Very old if unparseable

            temporal = math.pow(0.5, age_days / HALF_LIFE_DAYS)

            # Severity weight: failures weighted 1.5x
            base_severity = lesson.get("severity", 0.5)
            if lesson.get("type") == "failure":
                severity = base_severity * SEVERITY_WEIGHT
            else:
                severity = base_severity

            # Stage-match boost
            stage_boost = 1.0
            if current_stage and lesson.get("stage") == current_stage:
                stage_boost = STAGE_MATCH_BOOST

            score = temporal * severity * stage_boost

            scored_lesson = dict(lesson)
            scored_lesson["relevance_score"] = round(score, 4)
            scored.append(scored_lesson)

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:limit]

    def mark_applied(self, lesson_id: str) -> None:
        """
        Mark a lesson as applied (surfaced in a briefing).

        Increments applied_count and updates last_applied. Since the
        store is append-only, this writes a correction entry.
        """
        correction = {
            "id": lesson_id,
            "timestamp": _now_iso(),
            "type": "_applied",
            "applied_count_increment": 1,
        }
        self._append(correction)

    # -------------------------------------------------------------------
    # Bulk operations
    # -------------------------------------------------------------------

    def all_lessons(self) -> list[dict]:
        """Get all lessons (excluding correction entries)."""
        return [l for l in self._read_lessons()
                if l.get("type") != "_applied"]

    def by_stage(self, stage: str) -> list[dict]:
        """Get lessons for a specific stage."""
        return [l for l in self.all_lessons()
                if l.get("stage") == stage]

    def by_agent(self, agent: str) -> list[dict]:
        """Get lessons recorded by a specific agent."""
        return [l for l in self.all_lessons()
                if l.get("agent") == agent]

    def total_lessons(self) -> int:
        """Total number of real lessons (excluding corrections)."""
        return len(self.all_lessons())

    # -------------------------------------------------------------------
    # Briefing support
    # -------------------------------------------------------------------

    def summary_for_briefing(self, current_stage: str = "",
                             limit: int = 3) -> str:
        """
        Compact evolution summary for agent briefing injection.

        Returns the top N most relevant lessons as a brief string.
        """
        top = self.query(current_stage=current_stage, limit=limit)
        if not top:
            return "Evolution: No lessons recorded yet."

        lines = [f"Evolution lessons (top {len(top)} by relevance):"]
        for lesson in top:
            tag = lesson.get("type", "?")[0].upper()
            lines.append(
                f"  [{tag}] {lesson['lesson']} "
                f"(stage: {lesson.get('stage', '?')}, "
                f"rel: {lesson.get('relevance_score', 0):.2f})"
            )
        return "\n".join(lines)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
