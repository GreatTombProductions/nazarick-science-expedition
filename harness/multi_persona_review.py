#!/usr/bin/env python3
"""
Multi-persona review — single DSV4-Flash call evaluating from 3 perspectives.

Used by the validation pipeline for findings that need nuanced review
beyond what deterministic checks can provide. A single LLM call with
three distinct review personas achieves diverse coverage at minimal
token cost.

Layer 3 — Quality Infrastructure.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Called by the validation-officer agent's tool interface.
# The three personas are chosen to provide orthogonal evaluation angles.

import json


# The three review personas, chosen for orthogonal evaluation:
# 1. Domain expert (geological accuracy)
# 2. Methodological skeptic (process validity)
# 3. Data integrity auditor (evidence quality)
REVIEW_PERSONAS = [
    {
        "name": "Geologist",
        "perspective": (
            "Evaluate this finding from a geological perspective. "
            "Is the lithological classification consistent with known "
            "Kem Kem Group stratigraphy? Does the spectral signature "
            "match expected mineralogy?"
        ),
    },
    {
        "name": "Methods Reviewer",
        "perspective": (
            "Evaluate the methodology. Was the analysis approach "
            "appropriate for this claim? Are the confidence metrics "
            "well-calibrated? Would you accept this in peer review?"
        ),
    },
    {
        "name": "Data Auditor",
        "perspective": (
            "Evaluate the evidence chain. Is the data provenance clear? "
            "Could the finding be an artifact of cloud contamination, "
            "atmospheric effects, or sensor noise? Are tool versions "
            "and parameters documented?"
        ),
    },
]


def build_review_prompt(finding: dict) -> str:
    """
    Build the system prompt for a multi-persona review call.

    This produces a single prompt that asks DSV4-Flash to evaluate
    the finding from three perspectives sequentially. The output
    is structured for machine parsing.

    Args:
        finding: The finding dict to review.

    Returns:
        System prompt string for the review call.
    """
    finding_text = json.dumps(finding, indent=2, default=str)

    persona_sections = []
    for p in REVIEW_PERSONAS:
        persona_sections.append(
            f"### {p['name']}\n{p['perspective']}"
        )

    return (
        "You are reviewing a scientific finding from the Nazarick Science "
        "Expedition. Evaluate it from three distinct perspectives.\n\n"
        f"FINDING:\n```json\n{finding_text}\n```\n\n"
        "For each perspective, provide:\n"
        "- VERDICT: ACCEPT / CONCERN / REJECT\n"
        "- REASONING: One sentence explaining your verdict.\n\n"
        + "\n\n".join(persona_sections) + "\n\n"
        "Format your response as:\n"
        "GEOLOGIST: [VERDICT] — [reasoning]\n"
        "METHODS: [VERDICT] — [reasoning]\n"
        "AUDITOR: [VERDICT] — [reasoning]\n"
        "CONSENSUS: [ACCEPT/CONCERN/REJECT] — [one-sentence summary]"
    )


def parse_review_response(text: str) -> dict:
    """
    Parse the structured review response into a dict.

    Returns:
        {
            "geologist": {"verdict": str, "reasoning": str},
            "methods": {"verdict": str, "reasoning": str},
            "auditor": {"verdict": str, "reasoning": str},
            "consensus": {"verdict": str, "reasoning": str},
            "parse_success": bool,
        }
    """
    result = {
        "geologist": {"verdict": "UNKNOWN", "reasoning": ""},
        "methods": {"verdict": "UNKNOWN", "reasoning": ""},
        "auditor": {"verdict": "UNKNOWN", "reasoning": ""},
        "consensus": {"verdict": "UNKNOWN", "reasoning": ""},
        "parse_success": False,
    }

    if not text:
        return result

    import re

    labels = {
        "GEOLOGIST": "geologist",
        "METHODS": "methods",
        "AUDITOR": "auditor",
        "CONSENSUS": "consensus",
    }

    for label, key in labels.items():
        pattern = rf"{label}\s*:\s*(ACCEPT|CONCERN|REJECT)\s*[—\-]\s*(.+?)(?=\n[A-Z]+\s*:|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            result[key] = {
                "verdict": match.group(1).strip().upper(),
                "reasoning": match.group(2).strip(),
            }
            result["parse_success"] = True

    return result


def aggregate_verdicts(review: dict) -> str:
    """
    Aggregate individual verdicts into a final recommendation.

    Rules:
        - All ACCEPT → "VALIDATED"
        - Any REJECT → "REJECTED"
        - Mixed with CONCERN → "PRELIMINARY"
        - Parse failure → "PRELIMINARY" (fail open for findings)
    """
    if not review.get("parse_success", False):
        return "PRELIMINARY"

    verdicts = [
        review["geologist"]["verdict"],
        review["methods"]["verdict"],
        review["auditor"]["verdict"],
    ]

    if all(v == "ACCEPT" for v in verdicts):
        return "VALIDATED"
    if any(v == "REJECT" for v in verdicts):
        return "REJECTED"
    return "PRELIMINARY"
