#!/usr/bin/env python3
"""
Outer invocation loop: bridges orchestrator tasks to DSV4-Flash API calls.

Takes a task from orchestrator.cli_next(), builds the prompt, calls the
Gemini API, extracts structured output, and returns a result dict for
orchestrator.cli_record().

Layer 0 bridge + Layer 1b prompt assembly. System prompt built by
PromptBuilder (briefing_assembler + prompt_builder), which implements
the 5-section DSV4-Flash native architecture from prompt-architecture.md.

Layer 0 — completes the orchestrator foundation by closing the
"state machine works" → "expedition runs" gap.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: The bridge between deterministic orchestrator and LLM API.
# Prompt assembly delegated to PromptBuilder (Layer 1b).

import os
import logging
from pathlib import Path

from google import genai
from google.genai import types

from output_parser import parse_agent_output
from strip_thinking import strip_thinking_tags
from auto_fix import attempt_auto_fix
from prompt_builder import PromptBuilder

logger = logging.getLogger("nse.invoke")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
AGENTS_DIR = PROJECT_ROOT / "agents"

# DSV4-Flash model ID
DEFAULT_MODEL = "gemini-2.5-flash"

# Token limits for expedition-weight agents
MAX_OUTPUT_TOKENS = 8192
TEMPERATURE = 0.7

# Retry limits
MAX_RETRIES = 2


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

def _get_client() -> genai.Client:
    """
    Create a Gemini API client.

    Reads GOOGLE_AI_KEY from environment or from Renner's .env as fallback
    (shared key for the expedition during build phase).
    """
    api_key = os.environ.get("GOOGLE_AI_KEY")

    if not api_key:
        # Fallback: Renner's .env (shared during build phase)
        # harness/ → nse/ → central-mausoleum/ → 0th-floor-exterior/ → greattomb/
        env_path = Path(__file__).resolve().parents[4] / "agents" / "renner" / "climb" / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("GOOGLE_AI_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        raise RuntimeError(
            "GOOGLE_AI_KEY not found. Set in environment or place in "
            "agents/renner/climb/.env"
        )

    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# Prompt building — delegated to PromptBuilder (Layer 1b)
# ---------------------------------------------------------------------------

# Singleton prompt builder — created once per process
_prompt_builder = None

def _get_prompt_builder() -> PromptBuilder:
    """Get or create the prompt builder singleton."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder


def build_system_prompt(task: dict) -> str:
    """Build the system prompt via PromptBuilder (Layer 1b)."""
    return _get_prompt_builder().build_system_prompt(task)


def build_user_message(task: dict) -> str:
    """Build the user message via PromptBuilder (Layer 1b)."""
    return _get_prompt_builder().build_user_message(task)


# ---------------------------------------------------------------------------
# Invocation
# ---------------------------------------------------------------------------

def invoke_agent(task: dict, model: str = DEFAULT_MODEL,
                 dry_run: bool = False) -> dict:
    """
    Invoke a DSV4-Flash agent with the given task.

    Args:
        task: Task dict from orchestrator.cli_next()
        model: Gemini model ID
        dry_run: If True, return the prompt without calling the API

    Returns:
        Result dict for orchestrator.cli_record():
        {
            "findings": list,
            "status": dict,
            "next": str,
            "raw_output": str,
            "success": bool,
            "model": str,
            "usage": dict,
            "parse_success": bool,
        }
    """
    system_prompt = build_system_prompt(task)
    user_message = build_user_message(task)

    if dry_run:
        return {
            "findings": [],
            "status": {"mode": "dry_run"},
            "next": "",
            "raw_output": f"[DRY RUN]\nSystem: {system_prompt}\n\nUser: {user_message}",
            "success": True,
            "model": model,
            "usage": {},
            "parse_success": False,
        }

    client = _get_client()
    context = {"task": task, "model": model}

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                ),
            )

            # Extract text from response
            raw_text = ""
            if response.candidates and response.candidates[0].content:
                parts = response.candidates[0].content.parts
                # Filter out thinking parts
                visible = [p.text for p in parts
                          if hasattr(p, "text") and p.text
                          and not getattr(p, "thought", False)]
                raw_text = "\n".join(visible) if visible else ""

            if not raw_text and response.candidates:
                # Fallback: include all text parts
                parts = response.candidates[0].content.parts if response.candidates[0].content else []
                raw_text = "\n".join(p.text for p in parts
                                    if hasattr(p, "text") and p.text)

            # Strip thinking tags as additional safety
            clean_text = strip_thinking_tags(raw_text)

            # Parse structured output
            parsed = parse_agent_output(clean_text)

            # Extract usage metadata
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                usage = {
                    "prompt_tokens": getattr(um, "prompt_token_count", 0),
                    "output_tokens": getattr(um, "candidates_token_count", 0),
                    "total_tokens": getattr(um, "total_token_count", 0),
                }

            return {
                "findings": parsed["findings"],
                "status": parsed["status"],
                "next": parsed["next"],
                "raw_output": raw_text,
                "success": True,
                "model": model,
                "usage": usage,
                "parse_success": parsed["parse_success"],
            }

        except Exception as e:
            error_text = str(e)
            logger.warning(
                "Invocation attempt %d/%d failed for task %s: %s",
                attempt + 1, MAX_RETRIES + 1, task.get("id", "?"), error_text
            )

            # Try auto-fix
            fix_result = attempt_auto_fix(error_text, context)
            if fix_result["should_retry"] and attempt < MAX_RETRIES:
                logger.info("Auto-fix applied: %s. Retrying.", fix_result["action"])
                continue

            # All retries exhausted or fix says don't retry
            return {
                "findings": [],
                "status": {"error": error_text},
                "next": "",
                "raw_output": f"[ERROR] {error_text}",
                "success": False,
                "model": model,
                "usage": {},
                "parse_success": False,
                "error": error_text,
                "auto_fix": fix_result,
            }

    # Should not reach here, but safety
    return {
        "findings": [],
        "status": {"error": "max retries exceeded"},
        "next": "",
        "raw_output": "[ERROR] Max retries exceeded",
        "success": False,
        "model": model,
        "usage": {},
        "parse_success": False,
    }
