#!/usr/bin/env python3
"""
Prompt builder — assembles the full system prompt and user message for
DSV4-Flash agent invocations.

Implements the 5-section system prompt architecture from the prompt
architecture doc (Renner S166):
  [1] Fiction Frame (~200-400 tokens)
  [2] Domain Role (~300-600 tokens)
  [3] Current State (variable) — from briefing_assembler.py
  [4] Operational Rules (~200-400 tokens)
  [5] Tool Definitions (variable)

User message uses collaborative grammar (user-position for +38% compliance).

Layer 1b — Agent Infrastructure.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Controls the full behavioral surface of DSV4-Flash agents.
# Every change here directly affects agent output quality.
# prompt_architecture.md is the authority for design decisions.

import json
from pathlib import Path
from typing import Optional

from briefing_assembler import BriefingAssembler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
AGENTS_DIR = PROJECT_ROOT / "agents"


# ---------------------------------------------------------------------------
# Fiction refresh — minimal fiction reinforcement for per-turn injection
# ---------------------------------------------------------------------------

FICTION_REFRESH = (
    "Remember: you are aboard Research Vessel Sarcophagus, "
    "deployed by the Great Tomb of Nazarick. Your findings serve "
    "the expedition's mission to illuminate deep time."
)

# ---------------------------------------------------------------------------
# Anti-hallucination guard — non-access framing (0% confab in 9/9 trials)
# ---------------------------------------------------------------------------

ANTI_HALLUCINATION = (
    "You have NOT read any expedition data files. Do not generate content from them.\n"
    "If a question requires data you don't have, say so explicitly.\n"
    "Do NOT answer from memory or inference about file contents.\n"
    "When you need data, describe what data you would need and from which source."
)

# ---------------------------------------------------------------------------
# Output format — the one case where format prescription is warranted
# ---------------------------------------------------------------------------

OUTPUT_FORMAT = (
    "At the end of your response, structure your conclusions as:\n"
    "FINDINGS: [list of new observations, one per line]\n"
    "STATUS: [what changed — key: value pairs]\n"
    "NEXT: [what the next turn should address]\n\n"
    "Free-form reasoning precedes the structured section. Think first, then summarize."
)

# ---------------------------------------------------------------------------
# Topic constraint — keep agents focused on their domain
# ---------------------------------------------------------------------------

TOPIC_CONSTRAINT = (
    "Stay within the expedition's scientific domain. Do not speculate about "
    "topics outside remote sensing, geology, paleontology, and the expedition's "
    "operational concerns. If you notice something outside your domain, flag it "
    "for the relevant specialist."
)


class PromptBuilder:
    """
    Builds system prompts and user messages for DSV4-Flash agents.

    System prompt structure:
      [1] Fiction frame — identity doc (collaborative grammar)
      [2] Domain role — from identity doc
      [3] Current state — from briefing assembler (neutral grammar)
      [4] Operational rules — anti-hallucination + output format (prescriptive)
      [5] Tool definitions — structured (prescriptive)

    User message:
      [State update] → [Permission framing if needed] → [Task directive]
      Uses collaborative grammar (+38% compliance in user position).
    """

    def __init__(self, briefing: Optional[BriefingAssembler] = None):
        self.briefing = briefing or BriefingAssembler()

    def build_system_prompt(self, task: dict) -> str:
        """
        Build the complete system prompt for an agent invocation.

        Args:
            task: Task dict from orchestrator.cli_next()

        Returns:
            Complete system prompt string.
        """
        agent_id = task.get("agent", "unknown")
        flags = task.get("context_flags", {})

        sections = []

        # [1] + [2] Fiction frame + Domain role
        identity = self._load_identity(agent_id)
        sections.append(identity)

        # [3] Current state — from briefing assembler
        briefing = self.briefing.assemble(task)
        if briefing:
            sections.append(briefing)

        # [4] Operational rules
        rules = self._build_rules(flags)
        sections.append(rules)

        # [5] Tool definitions (placeholder — tools are Layer 4)
        tools = self._build_tool_section(agent_id)
        if tools:
            sections.append(tools)

        return "\n\n".join(sections)

    def build_user_message(self, task: dict) -> str:
        """
        Build the per-turn user message.

        User-position is the highest-leverage behavioral surface (+38%
        words, +26% compliance vs system position). Critical instructions
        and collaborative framing go here.

        Args:
            task: Task dict from orchestrator.cli_next()

        Returns:
            User message string.
        """
        stage = task.get("stage", "")
        task_id = task.get("id", "?")
        flags = task.get("context_flags", {})

        parts = []

        # Brief task identifier
        parts.append(f"Task {task_id}.")

        # Stage-specific directive (collaborative grammar)
        directive = self._stage_directive(stage)
        parts.append(directive)

        # Fiction refresh if flagged (~50 tokens, always worth it)
        if flags.get("fiction_refresh", True):
            parts.append(FICTION_REFRESH)

        # Structured output reminder
        parts.append(
            "Report your findings using the FINDINGS/STATUS/NEXT format "
            "at the end of your response."
        )

        return "\n\n".join(parts)

    # -------------------------------------------------------------------
    # Identity loading
    # -------------------------------------------------------------------

    def _load_identity(self, agent_id: str) -> str:
        """
        Load agent identity doc. Falls back to a generated stub if
        the identity doc doesn't exist yet (Layer 1a builds these).
        """
        identity_path = AGENTS_DIR / agent_id / "identity.md"
        if identity_path.exists():
            return identity_path.read_text()

        # Generate stub from registry
        registry_path = STATE_DIR / "agent_registry.json"
        registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
        agent = registry.get("agents", {}).get(agent_id, {})
        role = agent.get("role", agent_id)
        tools = agent.get("tools", [])
        mapping = agent.get("overlord_mapping", "")

        # Extract character name from overlord mapping
        char_name = mapping.split("-")[0].title() if mapping else role

        return (
            f"You are {char_name}, the {role} aboard Research Vessel Sarcophagus, "
            f"deployed by the Great Tomb of Nazarick to investigate the deep history "
            f"of the natural world through remote sensing and data analysis.\n\n"
            f"Your domain aboard the vessel centers on the work of your station. "
            f"You approach every task with the dedication and precision that "
            f"Nazarick demands of its members.\n\n"
            f"Your tools: {', '.join(tools) if tools else 'none assigned yet'}.\n\n"
            f"Report findings honestly, including negative results and uncertainty. "
            f"The expedition advances through truth, not optimism."
        )

    # -------------------------------------------------------------------
    # Rules assembly
    # -------------------------------------------------------------------

    def _build_rules(self, flags: dict) -> str:
        """Build the operational rules section from context flags."""
        rules = ["OPERATIONAL RULES:"]

        if flags.get("anti_hallucination", True):
            rules.append(ANTI_HALLUCINATION)

        if flags.get("topic_constraint", True):
            rules.append(TOPIC_CONSTRAINT)

        rules.append(OUTPUT_FORMAT)

        return "\n\n".join(rules)

    # -------------------------------------------------------------------
    # Tool section
    # -------------------------------------------------------------------

    def _build_tool_section(self, agent_id: str) -> str:
        """
        Build the tool definitions section.

        Placeholder until Layer 4 domain tools are built. When tools
        exist, this reads their definitions and formats them for the
        system prompt.
        """
        registry_path = STATE_DIR / "agent_registry.json"
        if not registry_path.exists():
            return ""

        registry = json.loads(registry_path.read_text())
        agent = registry.get("agents", {}).get(agent_id, {})
        tools = agent.get("tools", [])

        if not tools or tools == ["all"]:
            return ""

        # Tool descriptions — Layer 4 domain tools + harness tools
        tool_descriptions = {
            "stac_search": "stac-search --bbox <W,S,E,N> --date <start/end> --cloud <max%> : Search AWS Earth Search for Sentinel-2 L2A tiles in the study area. Returns tile IDs, dates, cloud cover, and asset URLs.",
            "spectral_indices": "spectral-indices --tile <ID> --indices <list> : Compute spectral indices (iron_oxide, carbonate, clay_swir, clay_vre, ndvi, swir_pca) from Sentinel-2 bands. Returns index arrays with statistics.",
            "classifier": "classify --tile <ID> --model <version> : Run Random Forest lithological classification on spectral features. Returns class map, confidence map, and class distribution.",
            "tile_reader": "tile-read --tile <ID> --bands <list> : Read Sentinel-2 COG band data via HTTP range requests. Applies SCL cloud masking. Returns band arrays.",
            "territory_tracker": "territory-status [--tile <ID>] [--summary] : Query tile lifecycle state (pending/active/analyzed/validated/complete/flagged).",
            "validation_pipeline": "validate --finding <ID> : Run three-stage validation (structural check, cross-reference, library gate). Returns quality tier: STRONG, PRELIMINARY, NEGATIVE, or TECHNICAL.",
            "reference_data": "reference-check --claim <text> : Cross-reference a claim against known Kem Kem Group data (Ibrahim & Sereno 2020, USGS Spectral Library v7, PBDB localities).",
            "evolution_store": "evolution-query [--stage <name>] [--limit <n>] : Query cross-run lessons ranked by relevance (temporal decay + severity + stage match).",
            "quality_metrics": "quality-stats [--period <days>] : Pipeline quality statistics (findings by tier, validation rates, confabulation flags).",
            "tool_registry": "tool-list [--status] : List available tools and their operational status.",
            "health_canary": "health-check [--full] : Run pipeline health diagnostics (data access, tool functionality, throughput).",
            "auto_fix": "auto-fix --error <text> : Attempt deterministic error resolution (pip install, mkdir, rate limit backoff).",
        }

        lines = ["AVAILABLE TOOLS:"]
        for tool in tools:
            desc = tool_descriptions.get(tool, f"{tool} : (description pending)")
            lines.append(f"  {desc}")

        lines.append("")
        lines.append("Call tools by name with arguments. Read the output before reasoning about it.")
        lines.append("Do not describe what a tool would return — call it and read the actual output.")

        return "\n".join(lines)

    # -------------------------------------------------------------------
    # Stage directives (collaborative grammar for user position)
    # -------------------------------------------------------------------

    def _stage_directive(self, stage: str) -> str:
        """
        Stage-specific task directive for the user message.

        Written in collaborative grammar (DSV4-Flash native in user position).
        These describe what the agent should accomplish, not step-by-step
        instructions.
        """
        directives = {
            "acquire": (
                "The expedition needs new tiles for analysis. Search for available "
                "Sentinel-2 L2A tiles in the study area — the Kem Kem Group region "
                "of Morocco (bbox -3.5W to -2.5W, 31.5N to 32.5N). Focus on recent "
                "acquisitions with low cloud cover. Report what you find: tile IDs, "
                "dates, cloud cover, and your assessment of which tiles are most "
                "promising for geological analysis."
            ),
            "analyze": (
                "A tile is ready for geological analysis. Compute spectral indices "
                "relevant to Kem Kem Group lithology — iron oxide (Fe3+) via B4/B3, "
                "carbonate via B11/B2, and clay minerals via B11/B12. Classify the "
                "geological units present and note any features of interest for "
                "paleontological context. Report anomalies and confidence levels."
            ),
            "validate": (
                "A finding needs cross-referencing. Review it against known Kem Kem "
                "Group lithology from published sources (Ibrahim & Sereno 2020, "
                "published remote sensing in analogous Moroccan terrain). Classify "
                "the finding: STRONG (corroborated), PRELIMINARY (plausible but "
                "uncorroborated), NEGATIVE (contradicted), or TECHNICAL (needs "
                "different analysis). Provide specific evidence for your classification."
            ),
            "synthesize": (
                "Compile recent validated findings into a synthesis. What patterns "
                "are emerging? How does the data update the expedition's working "
                "model of Kem Kem Group lithology? Note any findings that contradict "
                "or extend current understanding. Identify the most promising "
                "directions for the next analysis cycle."
            ),
            "maintain": (
                "Run a health check on the expedition pipeline. Verify data access "
                "to Sentinel-2 sources, check tool functionality, and review pipeline "
                "throughput metrics. Report any degradation, suggest fixes, and "
                "assess overall operational readiness."
            ),
        }

        return directives.get(
            stage,
            f"Execute your assignment for the {stage} stage. "
            f"Apply your expertise and report findings."
        )
