#!/usr/bin/env python3
"""
Extract structured output from DSV4-Flash agent responses.

Parses FINDINGS/STATUS/NEXT sections from agent output text.
The system prompt tells agents to produce these sections at the end
of their response for machine-parseable extraction.

Layer 0 — foundation dependency for invoke.py.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: All agent output flows through this parser. Grow patterns
# as new structured sections are added (e.g., HYPOTHESIS, TOOL_CALLS).

import re
from typing import Optional


def parse_agent_output(text: str) -> dict:
    """
    Extract structured sections from agent response text.

    Looks for FINDINGS:, STATUS:, NEXT: sections at the end of the
    response. Free-form reasoning precedes the structured section.

    Returns:
        {
            "findings": list[str],    # Individual finding statements
            "status": dict,           # Parsed status changes
            "next": str,              # Agent's suggested next target
            "raw_output": str,        # Full original text
            "parse_success": bool,    # Whether structured extraction worked
        }
    """
    result = {
        "findings": [],
        "status": {},
        "next": "",
        "raw_output": text,
        "parse_success": False,
    }

    if not text or not text.strip():
        return result

    # Extract FINDINGS section
    findings = _extract_section(text, "FINDINGS")
    if findings is not None:
        result["findings"] = _parse_list(findings)
        result["parse_success"] = True

    # Extract STATUS section
    status_text = _extract_section(text, "STATUS")
    if status_text is not None:
        result["status"] = _parse_status(status_text)
        result["parse_success"] = True

    # Extract NEXT section
    next_text = _extract_section(text, "NEXT")
    if next_text is not None:
        result["next"] = next_text.strip()
        result["parse_success"] = True

    return result


def _extract_section(text: str, section_name: str) -> Optional[str]:
    """
    Extract content following a section header like 'FINDINGS:' or 'FINDINGS -'.

    Handles multiple delimiter styles DSV4-Flash might produce:
      FINDINGS: content
      FINDINGS - content
      FINDINGS
      content

    Stops at the next section header or end of text.
    """
    # Known section names for boundary detection
    sections = ["FINDINGS", "STATUS", "NEXT", "HYPOTHESIS", "TOOL_CALLS"]
    boundary = "|".join(s for s in sections if s != section_name)

    # Pattern: section name followed by colon, dash, or newline
    pattern = rf"(?:^|\n)\s*{section_name}\s*[:\-]?\s*(.*?)(?=\n\s*(?:{boundary})\s*[:\-]|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()
    return None


def _parse_list(text: str) -> list[str]:
    """
    Parse a text block into a list of individual items.

    Handles:
      - Bullet lists (-, *, •)
      - Numbered lists (1., 2.)
      - Bracketed lists [item1, item2]
      - Plain text (returned as single-item list)
    """
    if not text.strip():
        return []

    # Try bullet/numbered list first
    items = re.findall(r"(?:^|\n)\s*(?:[-*•]|\d+\.)\s+(.+?)(?=\n\s*(?:[-*•]|\d+\.)\s|\Z)",
                       text, re.DOTALL)
    if items:
        return [item.strip() for item in items if item.strip()]

    # Try bracketed list
    bracket_match = re.match(r"\s*\[(.+)\]\s*$", text, re.DOTALL)
    if bracket_match:
        return [item.strip().strip("\"'") for item in bracket_match.group(1).split(",")
                if item.strip()]

    # Try comma-separated on a single line
    if "\n" not in text.strip() and "," in text:
        return [item.strip() for item in text.split(",") if item.strip()]

    # Fallback: each non-empty line is an item
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        return lines

    return [text.strip()] if text.strip() else []


def _parse_status(text: str) -> dict:
    """
    Parse status text into a dict of key-value pairs.

    Handles:
      - Key: value pairs
      - Key = value pairs
      - Plain text (stored under 'summary' key)
    """
    result = {}

    # Try key-value extraction
    kv_pairs = re.findall(r"(\w[\w\s]*\w)\s*[:=]\s*(.+?)(?=\n\s*\w[\w\s]*\w\s*[:=]|\Z)",
                          text, re.DOTALL)
    if kv_pairs:
        for key, value in kv_pairs:
            result[key.strip().lower().replace(" ", "_")] = value.strip()
        return result

    # Fallback: store as summary
    if text.strip():
        result["summary"] = text.strip()

    return result
