#!/usr/bin/env python3
"""
Briefing assembler — ephemeral per-turn context for DSV4-Flash agents.

Builds the state injection section of the agent's system prompt.
Uses context_flags from the orchestrator to selectively include state
sections, keeping the prompt token-efficient.

The briefing is ephemeral: regenerated every turn from live state.
The agent doesn't carry state — the harness carries it and projects
relevant slices per-turn. This is the novel contribution: harness-as-state-layer.

Layer 1b — Agent Infrastructure.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Highest-leverage component per intelligence brief.
# The briefing assembler determines what state each agent sees each turn.
# Changes here directly affect agent quality.

from pathlib import Path
from typing import Optional

from state_manager import StateManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"


class BriefingAssembler:
    """
    Assembles ephemeral per-turn briefing from live expedition state.

    Each invocation reads context_flags from the orchestrator task and
    builds a state injection string. Different stages get different
    state slices — an acquire agent needs territory status but not
    evolution lessons; a synthesize agent needs everything.

    The assembled briefing goes into the system prompt at position [3]
    (Current State) per the prompt architecture doc.
    """

    def __init__(self, state_mgr: Optional[StateManager] = None):
        self.state = state_mgr or StateManager()

    def assemble(self, task: dict) -> str:
        """
        Assemble the briefing for a specific task.

        Args:
            task: Task dict from orchestrator.cli_next() with:
                - agent: agent role ID
                - stage: pipeline stage name
                - context_flags: dict of boolean flags controlling inclusion

        Returns:
            Assembled briefing string for system prompt injection.
        """
        agent_id = task.get("agent", "unknown")
        stage = task.get("stage", "unknown")
        flags = task.get("context_flags", {})

        sections = []

        # Territory status — spatial state
        if flags.get("territory_status", False):
            territory = self.state.territory.summary_for_briefing()
            pending = self.state.territory.get_pending(limit=5)
            if pending:
                tile_list = ", ".join(
                    f"{t['id']} ({t['metadata'].get('cloud_cover', '?')}% cloud)"
                    for t in pending[:5]
                )
                territory += f"\nPending tiles: {tile_list}"
            sections.append(territory)

        # Recent findings — what's been discovered
        if flags.get("recent_findings", False):
            findings = self.state.territory.get_recent_findings(n=5)
            if findings:
                lines = ["Recent findings:"]
                for f in findings:
                    tile = f.get("tile_id", "?")
                    claim = f.get("claim", str(f))[:100]
                    conf = f.get("confidence", "?")
                    lines.append(f"  [{tile}] {claim} (confidence: {conf})")
                sections.append("\n".join(lines))
            else:
                sections.append("Recent findings: none yet.")

        # Evolution lessons — cross-run learning
        if flags.get("evolution_lessons", False):
            evo = self.state.evolution.summary_for_briefing(
                current_stage=stage, limit=3)
            if evo:
                sections.append(evo)

        # Tool registry — available tools for this agent
        if flags.get("tool_registry", False):
            tools = self._get_agent_tools(agent_id)
            if tools:
                sections.append(f"Available tools: {', '.join(tools)}")

        # Agent's previous activity
        last = self.state.journal.last_agent_entry(agent_id)
        if last:
            sections.append(
                f"Your last activity: {last.get('stage', '?')} stage, "
                f"{'succeeded' if last.get('success', True) else 'failed'}, "
                f"{last.get('findings_count', 0)} findings."
            )

        # Agent's research state (compressed)
        research = self.state.get_research_state(agent_id)
        if research and research.strip():
            # Truncate to last ~500 chars for token efficiency
            if len(research) > 500:
                research = "...\n" + research[-500:]
            sections.append(f"Your research notes:\n{research}")

        # Self-measurement summary — developmental trajectory
        if stage in ("synthesize", "maintain", "validate"):
            try:
                from metrics_collector import MetricsCollector
                mc = MetricsCollector()
                metrics_summary = mc.summary_for_briefing()
                sections.append(metrics_summary)
            except Exception:
                pass  # Metrics unavailable — non-blocking

        # Journal overview
        journal = self.state.journal.summary_for_briefing(hours=168)
        sections.append(journal)

        if not sections:
            return "Current state: expedition initializing. No prior data."

        return "\n\n".join(sections)

    def _get_agent_tools(self, agent_id: str) -> list[str]:
        """Get tool list for an agent from the registry."""
        import json
        registry_path = STATE_DIR / "agent_registry.json"
        if not registry_path.exists():
            return []
        registry = json.loads(registry_path.read_text())
        agent = registry.get("agents", {}).get(agent_id, {})
        return agent.get("tools", [])
