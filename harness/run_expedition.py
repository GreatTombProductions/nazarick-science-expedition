#!/usr/bin/env python3
"""
Main entry point for the Nazarick Science Expedition.

Drives the orchestrator loop:
    task = orchestrator.cli_next()
    result = invoke_agent(task)
    orchestrator.cli_record(task, result)

Bounded iteration, graceful shutdown, structured logging.

Layer 0 — the outer loop that makes the expedition run.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Entry point. Grows with harness features (streaming,
# Discord integration, audience governance) but core loop stays simple.

import argparse
import json
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add harness to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrator import Orchestrator
from invoke import invoke_agent, DEFAULT_MODEL

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
LOG_DIR = PROJECT_ROOT / "logs"

# Default iteration limits
DEFAULT_MAX_CYCLES = 5      # Bounded by default — override with --cycles
CYCLE_COOLDOWN = 2.0        # Seconds between cycles (rate limit protection)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(log_dir: Path, verbose: bool = False) -> logging.Logger:
    """Configure structured logging to file and console."""
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("nse")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Console handler — human-readable
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(console)

    # File handler — structured, append
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(
        log_dir / f"expedition_{timestamp}.log",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    ))
    logger.addHandler(file_handler)

    return logger


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

_shutdown_requested = False

def _handle_signal(signum, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    global _shutdown_requested
    _shutdown_requested = True
    logging.getLogger("nse").info(
        "Shutdown requested (signal %d). Finishing current cycle...", signum
    )

signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_expedition(
    max_cycles: int = DEFAULT_MAX_CYCLES,
    model: str = DEFAULT_MODEL,
    dry_run: bool = False,
    verbose: bool = False,
    single_stage: str = None,
) -> dict:
    """
    Run the expedition loop.

    Args:
        max_cycles: Maximum number of orchestrator cycles to run
        model: Gemini model ID to use
        dry_run: If True, build prompts but don't call the API
        verbose: Enable debug logging
        single_stage: If set, only run this stage (for testing)

    Returns:
        Summary dict with cycle count, successes, failures, findings.
    """
    logger = setup_logging(LOG_DIR, verbose)
    logger.info("=" * 60)
    logger.info("Nazarick Science Expedition — Starting")
    logger.info("Model: %s | Max cycles: %d | Dry run: %s",
                model, max_cycles, dry_run)
    logger.info("=" * 60)

    orchestrator = Orchestrator()

    # Ensure Layer 3 hooks are registered (idempotent — handles pre-existing state)
    orchestrator.register_hook("post_invoke", "confab_check")
    orchestrator.register_hook("post_invoke", "validation_gate")
    orchestrator.register_hook("post_invoke", "metrics_collect")

    status = orchestrator.status()
    logger.info("Orchestrator status: season=%s, cycle=%d",
                status["season"], status["cycle_count"])

    summary = {
        "started": datetime.now(timezone.utc).isoformat(),
        "cycles_attempted": 0,
        "cycles_succeeded": 0,
        "cycles_failed": 0,
        "total_findings": 0,
        "tasks": [],
        "model": model,
        "dry_run": dry_run,
    }

    for cycle in range(max_cycles):
        if _shutdown_requested:
            logger.info("Shutdown requested. Stopping after %d cycles.", cycle)
            break

        # Get next task
        task = orchestrator.cli_next()
        if task is None:
            logger.info("No more tasks available. Stopping.")
            break

        # Filter by stage if requested
        if single_stage and task.get("stage") != single_stage:
            # Record a skip and continue
            orchestrator.cli_record(task, {
                "findings": [],
                "status": {"skipped": f"stage filter: wanted {single_stage}"},
                "next": "",
                "raw_output": "[SKIPPED]",
                "success": True,
            })
            logger.info("Skipped task %s (stage %s != %s)",
                        task["id"], task["stage"], single_stage)
            continue

        logger.info("-" * 40)
        logger.info("Cycle %d/%d: task=%s stage=%s agent=%s",
                     cycle + 1, max_cycles, task["id"],
                     task["stage"], task["agent"])

        summary["cycles_attempted"] += 1

        # Invoke the agent
        t0 = time.monotonic()
        result = invoke_agent(task, model=model, dry_run=dry_run)
        elapsed = time.monotonic() - t0

        # Log result
        if result["success"]:
            summary["cycles_succeeded"] += 1
            summary["total_findings"] += len(result.get("findings", []))
            logger.info(
                "  SUCCESS in %.1fs — %d findings, parse=%s",
                elapsed, len(result.get("findings", [])),
                result.get("parse_success", False),
            )
            if result.get("findings"):
                for i, f in enumerate(result["findings"][:5], 1):
                    logger.info("    Finding %d: %s", i, f[:120])
            if result.get("usage"):
                logger.info("    Tokens: %s", json.dumps(result["usage"]))
        else:
            summary["cycles_failed"] += 1
            logger.warning(
                "  FAILED in %.1fs — %s",
                elapsed, result.get("error", "unknown error")[:200],
            )

        # Record with orchestrator
        orchestrator.cli_record(task, result)

        # Track in summary
        summary["tasks"].append({
            "id": task["id"],
            "stage": task["stage"],
            "agent": task["agent"],
            "success": result["success"],
            "findings_count": len(result.get("findings", [])),
            "elapsed": round(elapsed, 2),
            "parse_success": result.get("parse_success", False),
        })

        # Cooldown between cycles
        if cycle < max_cycles - 1 and not _shutdown_requested:
            time.sleep(CYCLE_COOLDOWN)

    summary["completed"] = datetime.now(timezone.utc).isoformat()

    # Run periodic metric aggregation (M2/M3/M4) at end of run
    try:
        from metrics_collector import MetricsCollector
        mc = MetricsCollector()
        agg_results = mc.run_periodic_aggregation()
        if agg_results:
            logger.info("Metrics aggregated: %s", ", ".join(agg_results.keys()))
            summary["metrics_aggregated"] = list(agg_results.keys())
    except Exception as e:
        logger.warning("Metrics aggregation failed: %s", e)

    # Final status
    logger.info("=" * 60)
    logger.info("Expedition run complete.")
    logger.info("  Cycles: %d attempted, %d succeeded, %d failed",
                summary["cycles_attempted"], summary["cycles_succeeded"],
                summary["cycles_failed"])
    logger.info("  Total findings: %d", summary["total_findings"])
    logger.info("=" * 60)

    # Write summary to file
    summary_path = LOG_DIR / "last_run_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, default=str))
    logger.info("Summary written to %s", summary_path)

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Nazarick Science Expedition — Outer Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 run_expedition.py --dry-run          # Test prompts without API calls\n"
            "  python3 run_expedition.py --cycles 1          # Single cycle\n"
            "  python3 run_expedition.py --stage acquire     # Only run acquire stage\n"
            "  python3 run_expedition.py --cycles 15 -v      # Full run with verbose logging\n"
        ),
    )

    parser.add_argument(
        "--cycles", type=int, default=DEFAULT_MAX_CYCLES,
        help=f"Max cycles to run (default: {DEFAULT_MAX_CYCLES})",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Gemini model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Build prompts but don't call the API",
    )
    parser.add_argument(
        "--stage", choices=["acquire", "analyze", "validate", "synthesize", "maintain"],
        help="Only run a specific stage (for testing)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show orchestrator status and exit",
    )
    parser.add_argument(
        "--metrics", action="store_true",
        help="Show self-measurement report and exit",
    )

    args = parser.parse_args()

    if args.status:
        orch = Orchestrator()
        print(json.dumps(orch.status(), indent=2))
        return

    if args.metrics:
        from metrics_collector import MetricsCollector
        mc = MetricsCollector()
        print(mc.full_report())
        return

    summary = run_expedition(
        max_cycles=args.cycles,
        model=args.model,
        dry_run=args.dry_run,
        verbose=args.verbose,
        single_stage=args.stage,
    )

    # Exit code: 0 if any succeeded, 1 if all failed
    if summary["cycles_attempted"] > 0 and summary["cycles_succeeded"] == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
