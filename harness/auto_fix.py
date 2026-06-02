#!/usr/bin/env python3
"""
Deterministic fixes before LLM escalation.

When an agent invocation fails with a known error pattern, try a
deterministic fix first. Only escalate to the LLM (or skip) if the
fix doesn't resolve the error.

Layer 5 — Coordination.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Called by orchestrator error handling. Grows as new
# error patterns are discovered during expedition operation.

import re
import subprocess
import time
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Fix implementations
# ---------------------------------------------------------------------------

def _fix_missing_module(error_text: str, context: dict) -> dict:
    """
    Extract module name from ImportError/ModuleNotFoundError and pip install it.
    """
    match = re.search(r"No module named '([^']+)'", error_text)
    if not match:
        match = re.search(r"ModuleNotFoundError: No module named (\S+)", error_text)
    if not match:
        return {"action": "Could not extract module name", "should_retry": False}

    module = match.group(1).split(".")[0]  # Top-level package

    # Safety: only install known expedition dependencies
    ALLOWED_MODULES = {
        "rasterio", "pystac_client", "pystac", "numpy", "scipy",
        "scikit-learn", "sklearn", "geopandas", "shapely", "fiona",
        "matplotlib", "folium", "pandas", "requests",
    }

    if module not in ALLOWED_MODULES:
        return {
            "action": f"Module '{module}' not in allowed list",
            "should_retry": False,
        }

    result = subprocess.run(
        ["pip", "install", module],
        capture_output=True, text=True, timeout=120,
    )

    if result.returncode == 0:
        return {"action": f"Installed {module}", "should_retry": True}
    else:
        return {
            "action": f"pip install {module} failed: {result.stderr[:200]}",
            "should_retry": False,
        }


def _fix_missing_directory(error_text: str, context: dict) -> dict:
    """
    Extract directory path from FileNotFoundError and create it.
    """
    match = re.search(r"FileNotFoundError.*?'([^']+)'", error_text)
    if not match:
        return {"action": "Could not extract path", "should_retry": False}

    path = Path(match.group(1))

    # Safety: only create directories within the project
    project_root = Path(__file__).resolve().parent.parent
    try:
        resolved = path.resolve()
        if not str(resolved).startswith(str(project_root)):
            return {
                "action": f"Path {path} outside project root",
                "should_retry": False,
            }
    except (OSError, ValueError):
        return {"action": f"Could not resolve path {path}", "should_retry": False}

    # Create the directory (or parent if path looks like a file)
    target = path if not path.suffix else path.parent
    target.mkdir(parents=True, exist_ok=True)

    return {"action": f"Created directory {target}", "should_retry": True}


def _fix_rate_limit(error_text: str, context: dict) -> dict:
    """
    Exponential backoff on rate limit errors.
    """
    retries = context.get("_rate_limit_retries", 0)
    max_retries = 3

    if retries >= max_retries:
        return {
            "action": f"Rate limit: max retries ({max_retries}) exceeded",
            "should_retry": False,
        }

    wait_seconds = min(30 * (2 ** retries), 300)  # 30s, 60s, 120s — cap at 5min
    time.sleep(wait_seconds)

    context["_rate_limit_retries"] = retries + 1
    return {
        "action": f"Rate limit: waited {wait_seconds}s (retry {retries + 1}/{max_retries})",
        "should_retry": True,
    }


def _fix_timeout(error_text: str, context: dict) -> dict:
    """
    Simple retry on timeout — the request may succeed on next attempt.
    """
    retries = context.get("_timeout_retries", 0)
    if retries >= 2:
        return {
            "action": "Timeout: max retries exceeded",
            "should_retry": False,
        }

    time.sleep(5)
    context["_timeout_retries"] = retries + 1
    return {
        "action": f"Timeout: retry {retries + 1}/2",
        "should_retry": True,
    }


# ---------------------------------------------------------------------------
# Registry — defined after fix functions
# ---------------------------------------------------------------------------

FIX_REGISTRY: list[dict] = [
    {
        "pattern": "ModuleNotFoundError",
        "match": lambda err: "ModuleNotFoundError" in err,
        "fix": _fix_missing_module,
        "description": "Install missing Python module via pip",
    },
    {
        "pattern": "FileNotFoundError",
        "match": lambda err: "FileNotFoundError" in err,
        "fix": _fix_missing_directory,
        "description": "Create missing directory",
    },
    {
        "pattern": "rate_limit",
        "match": lambda err: any(s in err.lower() for s in [
            "rate limit", "429", "quota exceeded", "resource exhausted",
        ]),
        "fix": _fix_rate_limit,
        "description": "Backoff retry after rate limit",
    },
    {
        "pattern": "timeout",
        "match": lambda err: any(s in err.lower() for s in [
            "timed out", "timeout", "deadline exceeded",
        ]),
        "fix": _fix_timeout,
        "description": "Simple retry on timeout",
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def attempt_auto_fix(error_text: str, context: Optional[dict] = None) -> dict:
    """
    Attempt to automatically fix a known error.

    Args:
        error_text: The error message/traceback from the failed invocation
        context: Optional dict with task context (stage, agent, etc.)

    Returns:
        {
            "fixed": bool,        # Whether a fix was applied
            "pattern": str,       # Which pattern matched (if any)
            "action": str,        # What the fix did
            "should_retry": bool, # Whether to retry the invocation
        }
    """
    for entry in FIX_REGISTRY:
        if entry["match"](error_text):
            try:
                result = entry["fix"](error_text, context or {})
                return {
                    "fixed": True,
                    "pattern": entry["pattern"],
                    "action": result.get("action", entry["description"]),
                    "should_retry": result.get("should_retry", True),
                }
            except Exception as e:
                return {
                    "fixed": False,
                    "pattern": entry["pattern"],
                    "action": f"Fix attempted but failed: {e}",
                    "should_retry": False,
                }

    return {
        "fixed": False,
        "pattern": None,
        "action": "No matching auto-fix pattern",
        "should_retry": False,
    }
