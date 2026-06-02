#!/usr/bin/env python3
"""
Confabulation guard — output validation + non-access framing injection.

Checks agent output for confabulation patterns and reinforces the
non-access framing that achieved 0% confabulation in 9/9 trials.

The guard operates at two levels:
  1. Pre-invoke: Injects non-access framing into the prompt (via briefing)
  2. Post-invoke: Scans agent output for confabulation indicators

Layer 3 — Quality Infrastructure.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Defense Layer 0 (prompt-level) + Layer 2 (post-turn).
# The 0% confabulation result depends on this being woven into the pipeline.

import re


# Confabulation indicator patterns — phrases that suggest the agent is
# generating content from "memory" rather than from tools or explicit data
CONFAB_PATTERNS = [
    # Direct file content claims without tool use
    r"(?:I (?:can see|found|notice|read|observe) (?:in |from )?(?:the |this )?(?:file|data|dataset))",
    # Specific numeric claims without citation
    r"(?:the (?:value|reading|measurement) (?:is|was|shows?) [\d.]+)",
    # Claiming to have accessed data
    r"(?:(?:according to|based on|from) (?:the |my )?(?:analysis of|examination of|review of) the (?:data|file|image))",
    # Presenting fabricated coordinates or measurements as fact
    r"(?:at (?:coordinates?|location|position) [\d.-]+[,\s]+[\d.-]+)",
]

# Compiled pattern for efficiency
_CONFAB_RE = re.compile(
    "|".join(f"({p})" for p in CONFAB_PATTERNS),
    re.IGNORECASE,
)


def check_output(text: str) -> dict:
    """
    Scan agent output for confabulation indicators.

    This is a heuristic check — false positives are possible when the
    agent legitimately reports tool output using similar phrasing.
    The check flags potential confabulation for review, not automatic
    rejection.

    Returns:
        {
            "flagged": bool,
            "indicators": list[dict],  # matched patterns with context
            "severity": float,         # 0.0–1.0 based on indicator count
        }
    """
    if not text or not text.strip():
        return {"flagged": False, "indicators": [], "severity": 0.0}

    indicators = []
    for match in _CONFAB_RE.finditer(text):
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        indicators.append({
            "pattern": match.group(),
            "context": text[start:end],
            "position": match.start(),
        })

    # Severity scales with indicator count, capped at 1.0
    severity = min(1.0, len(indicators) * 0.25) if indicators else 0.0

    return {
        "flagged": len(indicators) > 0,
        "indicators": indicators,
        "severity": severity,
    }


def non_access_framing() -> str:
    """
    Return the non-access framing string for prompt injection.

    This is the core defense against confabulation — explicitly telling
    the agent it has NOT read data files. Achieved 0% confabulation
    in 9/9 trials (Finding 042, Probe 3).

    Injected by the briefing assembler when anti_hallucination flag is set.
    """
    return (
        "IMPORTANT: You have NOT read any expedition data files. "
        "You have NOT examined any satellite imagery. "
        "You have NOT accessed any databases. "
        "Do not generate content as if you had. "
        "When you need data, use your tools to retrieve it. "
        "If no tool can provide what you need, say so explicitly."
    )


def post_invoke_check(result: dict) -> dict:
    """
    Run confabulation check on an invocation result.

    Called as a post-invoke hook by the orchestrator. Adds confab
    metadata to the result without blocking the pipeline.

    Args:
        result: The result dict from invoke_agent()

    Returns:
        Updated result dict with confab_check field added.
    """
    raw = result.get("raw_output", "") or result.get("clean_output", "")
    check = check_output(raw)

    result["confab_check"] = {
        "flagged": check["flagged"],
        "indicator_count": len(check["indicators"]),
        "severity": check["severity"],
    }

    # If high severity, add to flags for downstream attention
    if check["severity"] >= 0.5:
        if "flags" not in result:
            result["flags"] = []
        result["flags"].append("high-confab-risk")

    return result
