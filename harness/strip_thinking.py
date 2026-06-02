#!/usr/bin/env python3
"""
Strip <think>...</think> tags from DSV4-Flash output.

DSV4-Flash produces reasoning traces in <think> blocks that must be
removed before parsing structured output. One-liner utility.

Layer 0 — foundation dependency for orchestrator.py.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Called by orchestrator on every agent response.

import re

_THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_thinking_tags(text: str) -> str:
    """Remove all <think>...</think> blocks from text."""
    return _THINK_PATTERN.sub("", text).strip()
