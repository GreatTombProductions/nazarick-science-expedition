#!/usr/bin/env python3
"""
Unified state management facade + ideas backlog + research state compression.

Ties together territory_manager, journal_manager, and evolution_store into
a single interface the briefing assembler and orchestrator can use.

Also manages:
  - ideas_backlog.md (per-agent forced hypothesis capture)
  - research.md (per-agent harness-maintained compressed state)

Layer 2 — State Management Infrastructure.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: The facade other layers import. Briefing assembler (Layer 1b)
# reads state through this; orchestrator hooks write through it.

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from checkpoint import CheckpointManager
from territory_manager import TerritoryManager
from journal_manager import JournalManager
from evolution_store import EvolutionStore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
AGENTS_DIR = PROJECT_ROOT / "agents"

# Maximum lines for compressed research state
RESEARCH_STATE_MAX_LINES = 30


class StateManager:
    """
    Unified state management for the expedition harness.

    Provides a single point of access for all state operations:
    - Territory (tile lifecycle, spatial state)
    - Journal (research history, query)
    - Evolution (cross-run learning)
    - Ideas (per-agent hypothesis backlog)
    - Research (per-agent compressed state)
    """

    def __init__(self, checkpoint_mgr: Optional[CheckpointManager] = None):
        self.checkpoint = checkpoint_mgr or CheckpointManager(STATE_DIR)
        self.territory = TerritoryManager(self.checkpoint)
        self.journal = JournalManager()
        self.evolution = EvolutionStore(self.checkpoint)

    # -------------------------------------------------------------------
    # Ideas backlog — forced capture on hypothesis discard
    # -------------------------------------------------------------------

    def _ideas_path(self, agent_id: str) -> Path:
        """Path to an agent's ideas backlog."""
        return AGENTS_DIR / agent_id / "ideas_backlog.md"

    def capture_idea(self, agent_id: str, idea: str,
                     context: str = "", discarded_reason: str = "") -> None:
        """
        Record a discarded hypothesis or unexplored idea.

        Per the intelligence brief: forced capture on hypothesis discard.
        The agent is required to record ideas it doesn't pursue, so
        future sessions can evaluate them.

        Args:
            agent_id: Agent recording the idea
            idea: The hypothesis or idea
            context: What the agent was investigating when the idea arose
            discarded_reason: Why it wasn't pursued (resource, scope, priority)
        """
        path = self._ideas_path(agent_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        entry = (
            f"\n## {_now_short()} — {agent_id}\n"
            f"**Idea:** {idea}\n"
        )
        if context:
            entry += f"**Context:** {context}\n"
        if discarded_reason:
            entry += f"**Not pursued because:** {discarded_reason}\n"

        # Append to file
        if path.exists():
            content = path.read_text()
        else:
            content = f"# Ideas Backlog — {agent_id}\n\nHypotheses and ideas not pursued. Forced capture by harness.\n"

        content += entry
        self.checkpoint.write_atomic(path, content)

    def get_ideas(self, agent_id: str) -> str:
        """Get the full ideas backlog for an agent."""
        path = self._ideas_path(agent_id)
        if path.exists():
            return path.read_text()
        return ""

    def get_recent_ideas(self, agent_id: str, n: int = 5) -> list[str]:
        """Get the N most recent idea entries for an agent (raw sections)."""
        content = self.get_ideas(agent_id)
        if not content:
            return []
        # Split on ## headings
        sections = content.split("\n## ")[1:]  # Skip the header
        return [f"## {s}" for s in sections[-n:]]

    # -------------------------------------------------------------------
    # Research state — harness-maintained compressed state per agent
    # -------------------------------------------------------------------

    def _research_path(self, agent_id: str) -> Path:
        """Path to an agent's compressed research state."""
        return AGENTS_DIR / agent_id / "research.md"

    def update_research_state(self, agent_id: str, new_content: str) -> None:
        """
        Update an agent's compressed research state.

        The research state is a harness-maintained summary of what the
        agent knows and has done. Kept under RESEARCH_STATE_MAX_LINES
        by compressing older content.

        Args:
            agent_id: Agent whose state to update
            new_content: New lines to add to the research state
        """
        path = self._research_path(agent_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            existing = path.read_text()
        else:
            existing = f"# Research State — {agent_id}\n\n"

        # Append new content
        updated = existing.rstrip() + "\n\n" + new_content.strip() + "\n"

        # Compress if over limit
        lines = updated.split("\n")
        if len(lines) > RESEARCH_STATE_MAX_LINES:
            updated = self._compress_research_state(lines)

        self.checkpoint.write_atomic(path, updated)

    def _compress_research_state(self, lines: list[str]) -> str:
        """
        Compress research state to stay under the line limit.

        Strategy: keep the header and most recent content, compress
        the middle into a summary line. This preserves recency bias
        while maintaining the header context.
        """
        # Keep first 3 lines (header) and last 20 lines (recent)
        header = lines[:3]
        recent = lines[-20:]

        # Count compressed lines
        middle = lines[3:-20]
        compressed_count = len(middle)

        summary = [
            "",
            f"[{compressed_count} older lines compressed — "
            f"{_now_short()}]",
            "",
        ]

        return "\n".join(header + summary + recent)

    def get_research_state(self, agent_id: str) -> str:
        """Get an agent's current research state."""
        path = self._research_path(agent_id)
        if path.exists():
            return path.read_text()
        return ""

    # -------------------------------------------------------------------
    # Composite queries (for briefing assembly)
    # -------------------------------------------------------------------

    def full_briefing_state(self, agent_id: str, stage: str) -> dict:
        """
        Assemble all state relevant to an agent's current turn.

        Returns a dict of named state sections, each already formatted
        as a string ready for prompt injection.
        """
        return {
            "territory": self.territory.summary_for_briefing(),
            "journal": self.journal.summary_for_briefing(),
            "evolution": self.evolution.summary_for_briefing(
                current_stage=stage),
            "research_state": self.get_research_state(agent_id),
            "recent_ideas": "\n".join(self.get_recent_ideas(agent_id, n=3)),
            "recent_findings": _format_findings(
                self.territory.get_recent_findings(n=5)),
            "agent_last_entry": _format_entry(
                self.journal.last_agent_entry(agent_id)),
        }

    # -------------------------------------------------------------------
    # Post-turn state updates (called by orchestrator hooks)
    # -------------------------------------------------------------------

    def record_turn_results(self, task: dict, result: dict) -> None:
        """
        Update all state stores after an agent turn completes.

        Called by the orchestrator's post_invoke hook. Distributes
        the turn's results across territory, evolution, and research state.
        """
        agent = task.get("agent", "unknown")
        stage = task.get("stage", "unknown")

        # Update agent's research state with turn summary
        findings = result.get("findings", [])
        status = result.get("status", {})
        next_target = result.get("next", "")

        state_update = f"### Turn {task.get('id', '?')}\n"
        if findings:
            state_update += "Findings: " + "; ".join(
                str(f)[:80] for f in findings[:3]) + "\n"
        if status:
            state_update += "Status: " + json.dumps(status)[:120] + "\n"
        if next_target:
            state_update += f"Next: {next_target[:80]}\n"

        self.update_research_state(agent, state_update)

        # Record failures as evolution lessons
        if not result.get("success", True):
            error = result.get("error", str(status))
            self.evolution.record_lesson(
                stage=stage,
                agent=agent,
                lesson_type="failure",
                lesson=f"Turn failed: {error[:120]}",
                context=f"task={task.get('id', '?')}",
                severity=0.7,
            )


def _format_findings(findings: list[dict]) -> str:
    """Format findings list for briefing injection."""
    if not findings:
        return "No recent findings."
    lines = ["Recent findings:"]
    for f in findings:
        tile = f.get("tile_id", "?")
        claim = f.get("claim", str(f))[:100]
        lines.append(f"  - [{tile}] {claim}")
    return "\n".join(lines)


def _format_entry(entry: Optional[dict]) -> str:
    """Format a journal entry for briefing."""
    if not entry:
        return "No previous activity."
    return (
        f"Last activity: {entry.get('stage', '?')} stage, "
        f"{'succeeded' if entry.get('success', True) else 'failed'}, "
        f"{entry.get('findings_count', 0)} findings "
        f"({entry.get('timestamp', '?')[:19]})"
    )


def _now_short() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
