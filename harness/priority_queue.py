#!/usr/bin/env python3
"""
Signal-weighted agent scheduling for the expedition.

Simplified Grand Calculus: 2-3 signals determine which agent to invoke next.
Replaces orchestrator's default round-robin with informed selection.

Layer 5 — Coordination.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Plugs into orchestrator._select_agent() and _select_next_stage().

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

STATE_DIR = Path(__file__).resolve().parent.parent / "state"
AGENT_REGISTRY = STATE_DIR / "agent_registry.json"
TERRITORY_TRACKER = STATE_DIR / "territory_tracker.json"
JOURNAL = STATE_DIR / "journal.jsonl"


def score_agent(agent_id: str, stage: str) -> float:
    """
    Compute a priority score for an agent in a given stage.

    Signals (unitless, higher = more urgent):
      1. time_since_last_run: seconds since agent's last heartbeat / 3600
         — agents that haven't run recently get priority
      2. pending_work: count of pending items relevant to this agent
         — agents with queued work get priority
      3. stage_urgency: fixed weight per stage type
         — validation and synthesis get slight priority when work exists

    Returns a float score. Higher = invoke sooner.
    """
    registry = _load_json(AGENT_REGISTRY, {})
    agent = registry.get("agents", {}).get(agent_id, {})

    # Signal 1: Time since last run
    last_hb = agent.get("last_heartbeat")
    if last_hb:
        try:
            last_dt = datetime.fromisoformat(last_hb)
            elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
            time_score = min(elapsed / 3600.0, 24.0)  # Cap at 24 hours
        except (ValueError, TypeError):
            time_score = 12.0  # Default if parsing fails
    else:
        time_score = 24.0  # Never run = maximum urgency

    # Signal 2: Pending work items
    pending_score = _count_pending_work(stage)

    # Signal 3: Stage urgency weights
    stage_weights = {
        "acquire": 1.0,      # Tile acquisition — steady baseline
        "analyze": 1.5,      # Analysis — core work
        "validate": 2.0,     # Validation — findings waiting = high urgency
        "synthesize": 1.0,   # Synthesis — periodic
        "maintain": 0.5,     # Maintenance — low urgency unless issues
    }
    stage_score = stage_weights.get(stage, 1.0)

    return time_score + pending_score + stage_score


def score_stage(stage: str) -> float:
    """
    Compute priority score for a pipeline stage.

    Used by orchestrator to decide which stage to run next
    instead of simple round-robin.
    """
    pending = _count_pending_work(stage)
    weights = {
        "acquire": 1.0 + (5.0 if pending == 0 else 0.0),  # Boost if no pending tiles
        "analyze": 2.0 + pending * 0.5,     # Scale with pending tiles
        "validate": 3.0 + pending * 1.0,    # High priority when findings wait
        "synthesize": 1.0,                   # Periodic, low base
        "maintain": 0.5,                     # Background
    }
    return weights.get(stage, 1.0)


def select_next(stages: list[str], eligible_agents: dict[str, list[str]]) -> Optional[tuple[str, str]]:
    """
    Select the best (stage, agent) pair to invoke next.

    Args:
        stages: ordered list of stage names
        eligible_agents: stage → list of eligible agent role IDs

    Returns:
        (stage, agent_id) tuple, or None if nothing to schedule
    """
    best_score = -1.0
    best_pair = None

    for stage in stages:
        stage_priority = score_stage(stage)
        agents = eligible_agents.get(stage, [])

        for agent_id in agents:
            agent_priority = score_agent(agent_id, stage)
            combined = stage_priority * agent_priority
            if combined > best_score:
                best_score = combined
                best_pair = (stage, agent_id)

    return best_pair


def _count_pending_work(stage: str) -> float:
    """
    Count pending work items for a stage.

    Reads from territory_tracker for tile-related stages,
    from journal for validation-related stages.
    """
    if stage in ("acquire", "analyze"):
        tracker = _load_json(TERRITORY_TRACKER, {})
        tiles = tracker.get("tiles", {})
        if stage == "acquire":
            # Count how many tiles we DON'T have yet (proxy: low total)
            return max(0, 10 - len(tiles))  # Target: at least 10 tiles
        else:
            # Count tiles pending analysis
            return sum(
                1 for t in tiles.values()
                if t.get("status") == "pending"
            )

    elif stage == "validate":
        # Count unvalidated findings in journal
        findings = _count_recent_unvalidated()
        return float(findings)

    return 0.0


def _count_recent_unvalidated() -> int:
    """Count journal entries with findings that haven't been validated."""
    if not JOURNAL.exists():
        return 0

    count = 0
    try:
        for line in JOURNAL.read_text().strip().split("\n"):
            if not line:
                continue
            entry = json.loads(line)
            if (entry.get("stage") == "analyze"
                    and entry.get("findings_count", 0) > 0
                    and entry.get("success", False)):
                count += 1
    except (json.JSONDecodeError, OSError):
        pass
    return count


def _load_json(path: Path, default=None):
    """Load JSON file, returning default if missing."""
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return default if default is not None else {}
