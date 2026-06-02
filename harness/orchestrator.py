#!/usr/bin/env python3
"""
Deterministic orchestrator for the Nazarick Science Expedition.

The LLM does NOT decide what to do next — this state machine tells it.
Follows the cli_next()/cli_record() pattern from Sibyl (Kazuma 037 D6).
Parameter-gated: starts as bare loop, hooks added incrementally.

Layer 0 — must exist before anything else runs.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Core orchestrator. All other layers depend on this.

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from checkpoint import CheckpointManager
from strip_thinking import strip_thinking_tags

# ---------------------------------------------------------------------------
# Paths — all relative to project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
HARNESS_DIR = PROJECT_ROOT / "harness"
STATE_DIR = PROJECT_ROOT / "state"
AGENTS_DIR = PROJECT_ROOT / "agents"

EXPEDITION_STATE = STATE_DIR / "orchestrator_state.json"
AGENT_REGISTRY = STATE_DIR / "agent_registry.json"
JOURNAL = STATE_DIR / "journal.jsonl"


# ---------------------------------------------------------------------------
# Stage definitions — the expedition's fixed pipeline
# ---------------------------------------------------------------------------
# Each stage defines what kind of work happens and which agents are eligible.
# The orchestrator picks the next (stage, agent) pair; the agent executes.

STAGES = [
    "acquire",       # Scout acquires new tiles from STAC
    "analyze",       # Geologist/Analysts run spectral analysis on pending tiles
    "validate",      # Validation Officer cross-references findings
    "synthesize",    # Librarian compiles weekly synthesis
    "maintain",      # Pipeline Engineer runs health checks
]

# Stage → eligible agent roles (from expedition roster)
STAGE_AGENTS = {
    "acquire":   ["scout"],
    "analyze":   ["chief-geologist", "data-analyst", "field-surveyor-alpha",
                  "field-surveyor-beta"],
    "validate":  ["validation-officer"],
    "synthesize": ["research-librarian"],
    "maintain":  ["pipeline-engineer"],
}


class Orchestrator:
    """
    Deterministic state machine driving the expedition.

    Core loop:
        task = orchestrator.cli_next()
        # ... invoke agent with task ...
        orchestrator.cli_record(task, result)

    The orchestrator never calls the LLM directly. It produces task
    specifications; the outer loop handles invocation.
    """

    def __init__(self, checkpoint_mgr: Optional[CheckpointManager] = None):
        self.checkpoint = checkpoint_mgr or CheckpointManager(STATE_DIR)
        self._load_state()

    # -------------------------------------------------------------------
    # State management
    # -------------------------------------------------------------------

    def _load_state(self) -> None:
        """Load expedition state from disk, or initialize if missing."""
        if EXPEDITION_STATE.exists():
            self.state = json.loads(EXPEDITION_STATE.read_text())
        else:
            self.state = self._initial_state()
            self._save_state()

    def _initial_state(self) -> dict:
        """Create the initial expedition state document."""
        return {
            "version": 1,
            "season": "kem-kem-s1",
            "created": _now_iso(),
            "updated": _now_iso(),
            "cycle_count": 0,
            "current_stage": None,
            "current_agent": None,
            "last_completed": None,
            "hooks": {
                "pre_invoke": [],
                "post_invoke": [
                    "state_update",      # Layer 2: update state stores
                    "confab_check",      # Layer 3: confabulation detection
                    "validation_gate",   # Layer 3: finding quality classification
                    "metrics_collect",   # Self-measurement: per-turn tool usage
                ],
                "on_error": [],
            },
            "config": {
                "max_turns_per_cycle": 15,    # Bounded iteration
                "turn_budget_per_agent": 1,    # Single-turn agents at expedition weight
                "stage_order": STAGES,
            },
        }

    def _save_state(self) -> None:
        """Persist state atomically via checkpoint manager."""
        self.state["updated"] = _now_iso()
        self.checkpoint.write_atomic(
            EXPEDITION_STATE,
            json.dumps(self.state, indent=2, default=str),
        )

    # -------------------------------------------------------------------
    # Core API: cli_next / cli_record
    # -------------------------------------------------------------------

    def cli_next(self) -> Optional[dict]:
        """
        Return the next task to execute, or None if cycle is complete.

        Returns a task dict:
            {
                "id": str,           # unique task identifier
                "stage": str,        # pipeline stage name
                "agent": str,        # agent role to invoke
                "context_flags": {}, # what to include in briefing
                "created": str,      # ISO timestamp
            }
        """
        # Recovery: if a breadcrumb exists, we crashed mid-invocation
        recovered = self.checkpoint.recover_breadcrumb()
        if recovered:
            return recovered

        # Determine next stage via priority queue integration
        next_stage = self._select_next_stage()
        if next_stage is None:
            return None

        next_agent = self._select_agent(next_stage)
        if next_agent is None:
            return None

        task = {
            "id": f"{self.state['season']}-c{self.state['cycle_count']}-{next_stage}-{int(time.time())}",
            "stage": next_stage,
            "agent": next_agent,
            "context_flags": self._build_context_flags(next_stage),
            "created": _now_iso(),
        }

        # Leave breadcrumb before invocation — crash recovery
        self.checkpoint.write_breadcrumb(task)

        self.state["current_stage"] = next_stage
        self.state["current_agent"] = next_agent
        self._save_state()

        return task

    def cli_record(self, task: dict, result: dict) -> None:
        """
        Record completion of a task. Updates state and appends to journal.

        Args:
            task: The task dict from cli_next()
            result: Agent output dict with at minimum:
                {
                    "findings": list,    # extracted findings (may be empty)
                    "status": dict,      # state changes the agent reports
                    "next": str,         # agent's suggestion for next target
                    "raw_output": str,   # full agent response (pre-strip)
                    "success": bool,     # whether the turn succeeded
                }
        """
        # Strip thinking tags from raw output if present
        if "raw_output" in result:
            result["clean_output"] = strip_thinking_tags(result["raw_output"])

        # Run post-invoke hooks
        for hook in self.state["hooks"]["post_invoke"]:
            self._run_hook(hook, task, result)

        # Append to journal (append-only, never edited)
        journal_entry = {
            "task_id": task["id"],
            "stage": task["stage"],
            "agent": task["agent"],
            "success": result.get("success", True),
            "findings_count": len(result.get("findings", [])),
            "timestamp": _now_iso(),
        }
        _append_jsonl(JOURNAL, journal_entry)

        # Update state
        self.state["last_completed"] = {
            "task_id": task["id"],
            "stage": task["stage"],
            "agent": task["agent"],
            "timestamp": _now_iso(),
        }
        self.state["current_stage"] = None
        self.state["current_agent"] = None
        self.state["cycle_count"] += 1

        # Clear breadcrumb — task completed successfully
        self.checkpoint.clear_breadcrumb()
        self._save_state()

    # -------------------------------------------------------------------
    # Stage selection — dynamic scheduling on fixed pipeline
    # -------------------------------------------------------------------

    def _select_next_stage(self) -> Optional[str]:
        """
        Select the next stage to execute.

        Default: round-robin through stages. The priority_queue module
        (Layer 5) replaces this with signal-weighted selection once built.
        """
        stages = self.state["config"]["stage_order"]
        last = self.state.get("last_completed")

        if last is None:
            return stages[0]

        last_stage = last.get("stage", stages[0])
        try:
            idx = stages.index(last_stage)
            return stages[(idx + 1) % len(stages)]
        except ValueError:
            return stages[0]

    def _select_agent(self, stage: str) -> Optional[str]:
        """
        Select which agent to invoke for a given stage.

        Default: first eligible agent. Layer 5 priority_queue replaces
        this with signal-weighted selection (time since last run,
        pending work, unread messages).
        """
        eligible = STAGE_AGENTS.get(stage, [])
        if not eligible:
            return None

        # Load agent registry for recency-based selection
        registry = _load_json(AGENT_REGISTRY, default={})
        agents = registry.get("agents", {})

        # Pick the agent with the oldest last_run (or first if no data)
        best = None
        best_time = None
        for role in eligible:
            agent = agents.get(role, {})
            last_run = agent.get("last_heartbeat", "1970-01-01T00:00:00Z")
            if best_time is None or last_run < best_time:
                best = role
                best_time = last_run

        return best or eligible[0]

    # -------------------------------------------------------------------
    # Context flags — what the briefing assembler should include
    # -------------------------------------------------------------------

    def _build_context_flags(self, stage: str) -> dict:
        """
        Build context flags for the briefing assembler.

        These boolean flags control what gets injected into the agent's
        prompt. Different stages need different context slices.
        """
        return {
            "territory_status": stage in ("acquire", "analyze"),
            "recent_findings": stage in ("analyze", "validate", "synthesize"),
            "evolution_lessons": stage in ("analyze", "validate"),
            "tool_registry": stage in ("analyze", "maintain"),
            "anti_hallucination": True,   # Always inject
            "topic_constraint": True,     # Always inject
            "fiction_refresh": True,      # ~50 tokens, always inject
        }

    # -------------------------------------------------------------------
    # Hook system — parameter-gated extensibility
    # -------------------------------------------------------------------

    def register_hook(self, phase: str, hook_name: str) -> None:
        """Register a hook to fire at a specific phase."""
        if phase in self.state["hooks"]:
            if hook_name not in self.state["hooks"][phase]:
                self.state["hooks"][phase].append(hook_name)
                self._save_state()

    def _run_hook(self, hook_name: str, task: dict, result: dict) -> None:
        """
        Execute a named hook. Hooks are Python callables registered by name.

        Built-in hooks:
          - "state_update": Updates state management stores (Layer 2)
        """
        if hook_name == "state_update":
            try:
                from state_manager import StateManager
                sm = StateManager(self.checkpoint)
                sm.record_turn_results(task, result)
            except Exception:
                pass  # State update failure should not block pipeline
        elif hook_name == "confab_check":
            try:
                from confab_guard import post_invoke_check
                post_invoke_check(result)
            except Exception:
                pass  # Confab check failure should not block pipeline
        elif hook_name == "validation_gate":
            try:
                from validation_pipeline import ValidationPipeline
                vp = ValidationPipeline(self.checkpoint)
                for finding in result.get("findings", []):
                    if isinstance(finding, dict) and "claim" in finding:
                        vp.validate(finding)
            except Exception:
                pass  # Validation failure should not block pipeline
        elif hook_name == "metrics_collect":
            try:
                from metrics_collector import MetricsCollector
                mc = MetricsCollector()
                mc.post_invoke_collect(task, result)
            except Exception:
                pass  # Metrics failure should not block pipeline

    # -------------------------------------------------------------------
    # Introspection
    # -------------------------------------------------------------------

    def status(self) -> dict:
        """Return current orchestrator status for display/debugging."""
        return {
            "season": self.state["season"],
            "cycle_count": self.state["cycle_count"],
            "current_stage": self.state["current_stage"],
            "current_agent": self.state["current_agent"],
            "last_completed": self.state.get("last_completed"),
            "registered_hooks": {
                k: len(v) for k, v in self.state["hooks"].items()
            },
        }


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """UTC ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, default: Any = None) -> Any:
    """Load JSON file, returning default if missing."""
    if path.exists():
        return json.loads(path.read_text())
    return default if default is not None else {}


def _append_jsonl(path: Path, entry: dict) -> None:
    """Append a single JSON line to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------

def main():
    """CLI for manual orchestrator interaction."""
    import argparse

    parser = argparse.ArgumentParser(description="NSE Orchestrator")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("next", help="Get next task")
    sub.add_parser("status", help="Show orchestrator status")

    record_p = sub.add_parser("record", help="Record task completion")
    record_p.add_argument("task_id", help="Task ID to record")
    record_p.add_argument("--success", action="store_true", default=True)

    sub.add_parser("init", help="Initialize state (reset)")

    args = parser.parse_args()

    orch = Orchestrator()

    if args.command == "next":
        task = orch.cli_next()
        if task:
            print(json.dumps(task, indent=2))
        else:
            print("No tasks available.")
    elif args.command == "status":
        print(json.dumps(orch.status(), indent=2))
    elif args.command == "init":
        # Reset state
        if EXPEDITION_STATE.exists():
            EXPEDITION_STATE.unlink()
        orch = Orchestrator()
        print("State initialized.")
        print(json.dumps(orch.status(), indent=2))
    elif args.command == "record":
        # Minimal record for CLI testing
        orch.cli_record(
            {"id": args.task_id, "stage": "manual", "agent": "manual"},
            {"findings": [], "status": {}, "next": "", "success": args.success},
        )
        print(f"Recorded: {args.task_id}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
