#!/usr/bin/env python3
"""
Self-measurement infrastructure — M1 through M6 metrics collection.

Tracks the expedition's developmental trajectory claim:
"The system gets measurably better over time not because the model improves
but because the ecosystem matures."

Six metrics, three developmental mechanisms, automatic + manual collection.

Layer 3/4 bridge — Quality Infrastructure meets Domain Tools.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Self-measurement IS the expedition's scientific claim about
# itself. The geological findings are science about the world; this is science
# about autoresearch. Both are real. Both contribute to human knowledge.

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nse.metrics")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
METRICS_DIR = PROJECT_ROOT / "metrics"

# JSONL file paths per metric
METRIC_FILES = {
    "m1_classification_accuracy": METRICS_DIR / "classification-accuracy.jsonl",
    "m2_throughput":              METRICS_DIR / "throughput.jsonl",
    "m3_validation_rate":        METRICS_DIR / "validation-rate.jsonl",
    "m4_tool_reuse":             METRICS_DIR / "tool-reuse.jsonl",
    "m5_council_quality":        METRICS_DIR / "council-quality.jsonl",
    "m6_baseline_comparison":    METRICS_DIR / "baseline-comparison.jsonl",
}

# Tool-to-role eligibility for M4 reuse rate calculation
TOOL_ROLE_ELIGIBILITY = {
    "stac_search":       ["scout", "data-analyst"],
    "tile_reader":       ["chief-geologist", "field-surveyor-alpha",
                          "field-surveyor-beta", "data-analyst"],
    "spectral_indices":  ["chief-geologist", "field-surveyor-alpha",
                          "field-surveyor-beta"],
    "classifier":        ["chief-geologist", "data-analyst"],
}


class MetricsCollector:
    """
    Collects and stores M1-M6 self-measurement metrics.

    Automatic metrics (M1-M4) are collected as byproducts of normal
    operation via orchestrator hooks. Manual metrics (M5-M6) are
    recorded via explicit method calls.

    All entries are append-only JSONL with consistent schema:
    {
        "timestamp": ISO-8601,
        "measurement_period": description of time window,
        "values": metric-specific values,
        "context": optional metadata,
    }
    """

    def __init__(self):
        METRICS_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------
    # M1: Classification Accuracy
    # -------------------------------------------------------------------

    def record_classification_accuracy(
        self,
        model_version: str,
        train_accuracy: float,
        holdout_accuracy: float,
        per_class: dict,
        n_train: int,
        n_holdout: int,
        feature_importance: list,
    ) -> dict:
        """
        Record M1 after a classifier retrain event.

        Called by LithologyClassifier.train() or post-retrain hook.
        Mechanism tested: primarily A (tool improvement).

        Returns the recorded entry.
        """
        entry = {
            "timestamp": _now_iso(),
            "measurement_period": f"retrain-{model_version}",
            "values": {
                "train_accuracy": train_accuracy,
                "holdout_accuracy": holdout_accuracy,
                "per_class_f1": {
                    k: v.get("f1-score", 0.0)
                    for k, v in per_class.items()
                    if isinstance(v, dict) and "f1-score" in v
                },
                "macro_f1": _macro_f1(per_class),
                "n_train": n_train,
                "n_holdout": n_holdout,
            },
            "context": {
                "model_version": model_version,
                "top_features": [f["feature"] for f in feature_importance[:5]],
            },
        }
        _append_metric("m1_classification_accuracy", entry)
        logger.info(
            "M1 recorded: %s holdout=%.3f macro_f1=%.3f (%d samples)",
            model_version, holdout_accuracy,
            entry["values"]["macro_f1"], n_holdout,
        )
        return entry

    # -------------------------------------------------------------------
    # M2: Analysis Throughput
    # -------------------------------------------------------------------

    def record_throughput(
        self,
        period_start: str,
        period_end: str,
        tiles_entered: int,
        tiles_completed: int,
        total_tiles: int,
    ) -> dict:
        """
        Record M2 throughput for a measurement period.

        Computed from territory tracker timestamps.
        Mechanism tested: A (faster tools) and C (better coordination).

        Returns the recorded entry.
        """
        # Calculate daily rate
        try:
            start = datetime.fromisoformat(period_start)
            end = datetime.fromisoformat(period_end)
            days = max((end - start).total_seconds() / 86400, 0.001)
            daily_rate = tiles_completed / days
        except (ValueError, TypeError):
            days = 0.0
            daily_rate = 0.0

        entry = {
            "timestamp": _now_iso(),
            "measurement_period": f"{period_start[:10]} to {period_end[:10]}",
            "values": {
                "tiles_entered": tiles_entered,
                "tiles_completed": tiles_completed,
                "days": round(days, 2),
                "daily_rate": round(daily_rate, 3),
                "total_tiles_in_system": total_tiles,
            },
            "context": {},
        }
        _append_metric("m2_throughput", entry)
        logger.info(
            "M2 recorded: %d completed in %.1f days (%.2f/day), %d total",
            tiles_completed, days, daily_rate, total_tiles,
        )
        return entry

    # -------------------------------------------------------------------
    # M3: Finding Validation Rate
    # -------------------------------------------------------------------

    def record_validation_rate(
        self,
        period_start: str,
        period_end: str,
        validated: int,
        preliminary: int,
        rejected: int,
        novel: int,
        incomplete: int,
    ) -> dict:
        """
        Record M3 validation rate for a measurement period.

        Computed from validation pipeline output.
        Mechanism tested: primarily B (lineage) and A (better tools).

        Returns the recorded entry.
        """
        total_judged = validated + rejected
        validation_rate = validated / total_judged if total_judged > 0 else 0.0
        total_submitted = validated + preliminary + rejected + novel + incomplete

        entry = {
            "timestamp": _now_iso(),
            "measurement_period": f"{period_start[:10]} to {period_end[:10]}",
            "values": {
                "validated": validated,
                "preliminary": preliminary,
                "rejected": rejected,
                "novel": novel,
                "incomplete": incomplete,
                "total_submitted": total_submitted,
                "validation_rate": round(validation_rate, 4),
            },
            "context": {},
        }
        _append_metric("m3_validation_rate", entry)
        logger.info(
            "M3 recorded: %.1f%% validation rate (%d/%d judged), %d total",
            validation_rate * 100, validated, total_judged, total_submitted,
        )
        return entry

    # -------------------------------------------------------------------
    # M4: Tool Reuse Rate
    # -------------------------------------------------------------------

    def record_tool_reuse(
        self,
        tool_name: str,
        heartbeats_since_deploy: int,
        invocations: int,
        eligible_heartbeats: int,
        deployer: str = "",
    ) -> dict:
        """
        Record M4 reuse rate for a specific tool.

        Computed from tool invocation logs.
        Mechanism tested: primarily C (harness) and A (useful tools).

        Returns the recorded entry.
        """
        reuse_rate = (invocations / eligible_heartbeats
                      if eligible_heartbeats > 0 else 0.0)

        entry = {
            "timestamp": _now_iso(),
            "measurement_period": f"since deploy ({heartbeats_since_deploy} heartbeats)",
            "values": {
                "tool": tool_name,
                "heartbeats_since_deploy": heartbeats_since_deploy,
                "invocations": invocations,
                "eligible_heartbeats": eligible_heartbeats,
                "reuse_rate": round(reuse_rate, 4),
            },
            "context": {
                "deployer": deployer,
                "eligible_roles": TOOL_ROLE_ELIGIBILITY.get(tool_name, []),
            },
        }
        _append_metric("m4_tool_reuse", entry)
        logger.info(
            "M4 recorded: %s reuse=%.1f%% (%d/%d eligible)",
            tool_name, reuse_rate * 100, invocations, eligible_heartbeats,
        )
        return entry

    # -------------------------------------------------------------------
    # M5: Council Decision Quality (manual)
    # -------------------------------------------------------------------

    def record_council_quality(
        self,
        poll_id: str,
        num_options: int,
        specificity_score: float,
        evidence_citations: int,
        assessor: str = "titus-expedition",
        notes: str = "",
    ) -> dict:
        """
        Record M5 council/poll quality assessment.

        Manual assessment by Titus-expedition during weekly synthesis.
        Mechanism tested: all three, primarily B and C.

        Args:
            poll_id: Identifier for the governance poll
            num_options: How many concrete options were presented
            specificity_score: 1-5 subjective (1=vague, 5=actionable)
            evidence_citations: How many validated findings cited in rationales
            assessor: Who performed the assessment
            notes: Optional qualitative observations

        Returns the recorded entry.
        """
        entry = {
            "timestamp": _now_iso(),
            "measurement_period": f"poll-{poll_id}",
            "values": {
                "poll_id": poll_id,
                "num_options": num_options,
                "specificity_score": specificity_score,
                "evidence_citations": evidence_citations,
            },
            "context": {
                "assessor": assessor,
                "notes": notes,
            },
        }
        _append_metric("m5_council_quality", entry)
        logger.info(
            "M5 recorded: poll=%s options=%d specificity=%.1f citations=%d",
            poll_id, num_options, specificity_score, evidence_citations,
        )
        return entry

    # -------------------------------------------------------------------
    # M6: Multi-Agent vs Single-Agent Baseline (manual)
    # -------------------------------------------------------------------

    def record_baseline_comparison(
        self,
        comparison_id: str,
        task_description: str,
        multi_agent_findings: int,
        single_agent_findings: int,
        multi_agent_validated: int,
        single_agent_validated: int,
        multi_agent_metrics_computed: int,
        single_agent_metrics_computed: int,
        mode_mixing_indicators: dict,
        notes: str = "",
    ) -> dict:
        """
        Record M6 monthly baseline comparison.

        Dedicated measurement heartbeat — one extra invocation per month.
        Cost: ~$0.05 per comparison. This IS the cleanest test of the
        mode purity thesis (PRE-4).

        Args:
            comparison_id: Unique identifier (e.g., "2026-06-monthly")
            task_description: What task was given to both conditions
            multi_agent_*: Metrics from the expedition's pipeline
            single_agent_*: Metrics from the single-agent control
            mode_mixing_indicators: Qualitative observations about
                mode mixing in the single-agent condition

        Returns the recorded entry.
        """
        # Compute advantage metrics
        finding_advantage = (
            (multi_agent_findings - single_agent_findings) /
            max(single_agent_findings, 1)
        )
        validation_advantage = (
            (multi_agent_validated - single_agent_validated) /
            max(single_agent_validated, 1)
        )

        entry = {
            "timestamp": _now_iso(),
            "measurement_period": f"comparison-{comparison_id}",
            "values": {
                "comparison_id": comparison_id,
                "multi_agent": {
                    "findings": multi_agent_findings,
                    "validated": multi_agent_validated,
                    "metrics_computed": multi_agent_metrics_computed,
                },
                "single_agent": {
                    "findings": single_agent_findings,
                    "validated": single_agent_validated,
                    "metrics_computed": single_agent_metrics_computed,
                },
                "advantage": {
                    "finding_ratio": round(finding_advantage, 3),
                    "validation_ratio": round(validation_advantage, 3),
                },
                "mode_mixing_indicators": mode_mixing_indicators,
            },
            "context": {
                "task": task_description,
                "notes": notes,
            },
        }
        _append_metric("m6_baseline_comparison", entry)
        logger.info(
            "M6 recorded: %s — multi=%d/%d vs single=%d/%d findings/validated",
            comparison_id, multi_agent_findings, multi_agent_validated,
            single_agent_findings, single_agent_validated,
        )
        return entry

    # -------------------------------------------------------------------
    # Aggregation — compute metrics from existing state
    # -------------------------------------------------------------------

    def compute_throughput_from_territory(self, territory_data: dict,
                                          days: int = 7) -> dict:
        """
        Compute M2 throughput from territory tracker data.

        Examines tile history entries to count transitions within
        the measurement window.

        Args:
            territory_data: Full territory_tracker.json content
            days: Rolling window size (default 7 days)

        Returns:
            Throughput stats dict (ready for record_throughput).
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        tiles = territory_data.get("tiles", {})
        entered = 0
        completed = 0

        for tile in tiles.values():
            # Check if tile entered pipeline during window
            added = tile.get("added", "")
            if added >= cutoff_iso:
                entered += 1

            # Check if tile reached validated/complete during window
            for h in tile.get("history", []):
                if (h.get("timestamp", "") >= cutoff_iso and
                        h.get("status") in ("validated", "complete")):
                    completed += 1
                    break  # Count each tile once

        return {
            "period_start": cutoff.isoformat(),
            "period_end": now.isoformat(),
            "tiles_entered": entered,
            "tiles_completed": completed,
            "total_tiles": len(tiles),
        }

    def compute_validation_rate_from_log(self, findings_log_path: Path,
                                          days: int = 7) -> dict:
        """
        Compute M3 validation rate from the findings log.

        Args:
            findings_log_path: Path to findings_log.jsonl
            days: Rolling window size (default 7 days)

        Returns:
            Validation rate stats dict (ready for record_validation_rate).
        """
        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(days=days)).isoformat()

        counts = {
            "VALIDATED": 0,
            "PRELIMINARY": 0,
            "REJECTED": 0,
            "NOVEL": 0,
            "INCOMPLETE": 0,
        }

        if findings_log_path.exists():
            for line in findings_log_path.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts = entry.get("timestamp", "")
                if ts < cutoff:
                    continue

                classification = entry.get("classification", "").upper()
                if classification in counts:
                    counts[classification] += 1

        return {
            "period_start": cutoff,
            "period_end": now.isoformat(),
            "validated": counts["VALIDATED"],
            "preliminary": counts["PRELIMINARY"],
            "rejected": counts["REJECTED"],
            "novel": counts["NOVEL"],
            "incomplete": counts["INCOMPLETE"],
        }

    def compute_tool_reuse_from_journal(self, journal_path: Path) -> dict:
        """
        Compute M4 tool reuse rates from the journal.

        Scans journal entries for tool invocation patterns. Returns
        stats per tool for recording.

        Args:
            journal_path: Path to journal.jsonl

        Returns:
            Dict of tool_name → reuse stats.
        """
        if not journal_path.exists():
            return {}

        # Count total heartbeats per role and tool invocations per entry
        role_heartbeats: dict[str, int] = {}
        tool_invocations: dict[str, int] = {}

        for line in journal_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            agent = entry.get("agent", "")
            stage = entry.get("stage", "")

            # Count heartbeats per agent role
            role_heartbeats[agent] = role_heartbeats.get(agent, 0) + 1

            # Infer tool usage from stage
            # acquire stage → stac_search
            # analyze stage → spectral_indices, tile_reader, classifier
            # validate stage → validation_pipeline
            stage_tools = {
                "acquire": ["stac_search"],
                "analyze": ["spectral_indices", "tile_reader", "classifier"],
            }
            for tool in stage_tools.get(stage, []):
                tool_invocations[tool] = tool_invocations.get(tool, 0) + 1

        # Compute reuse rates
        results = {}
        total_heartbeats = sum(role_heartbeats.values())

        for tool, eligible_roles in TOOL_ROLE_ELIGIBILITY.items():
            eligible_hb = sum(role_heartbeats.get(r, 0)
                              for r in eligible_roles)
            invocations = tool_invocations.get(tool, 0)
            results[tool] = {
                "heartbeats_since_deploy": total_heartbeats,
                "invocations": invocations,
                "eligible_heartbeats": eligible_hb,
            }

        return results

    # -------------------------------------------------------------------
    # Orchestrator hook — per-turn metric collection
    # -------------------------------------------------------------------

    def post_invoke_collect(self, task: dict, result: dict) -> None:
        """
        Collect metrics as a post-invoke hook in the orchestrator.

        This is the automatic collection path for M2, M3, and M4.
        Runs after every agent turn. Lightweight — no API calls,
        just bookkeeping.
        """
        stage = task.get("stage", "")
        success = result.get("success", False)

        if not success:
            return

        # Track tool usage in per-turn log (M4 accumulation)
        tool_log_path = METRICS_DIR / "tool-usage-raw.jsonl"
        tools_used = _infer_tools_from_stage(stage)
        if tools_used:
            tool_entry = {
                "timestamp": _now_iso(),
                "task_id": task.get("id", ""),
                "agent": task.get("agent", ""),
                "stage": stage,
                "tools_used": tools_used,
            }
            _append_jsonl(tool_log_path, tool_entry)

        # Track findings for M3 (count is already in the journal;
        # detailed classification is in findings_log via validation hook)
        findings_count = len(result.get("findings", []))
        if findings_count > 0:
            logger.debug(
                "Metrics: %d findings from %s/%s",
                findings_count, stage, task.get("agent", "?"),
            )

    # -------------------------------------------------------------------
    # Periodic aggregation — called by nightly/on-demand script
    # -------------------------------------------------------------------

    def run_periodic_aggregation(self) -> dict:
        """
        Run all automatic metric aggregations.

        Intended to be called periodically (e.g., after each expedition
        run or nightly). Computes M2, M3, M4 from current state and
        records them.

        Returns:
            Dict of metric_name → recorded entry.
        """
        results = {}

        # M2: Throughput from territory tracker
        territory_path = STATE_DIR / "territory_tracker.json"
        if territory_path.exists():
            territory_data = json.loads(territory_path.read_text())
            tp_stats = self.compute_throughput_from_territory(territory_data)
            if tp_stats["total_tiles"] > 0:
                results["m2"] = self.record_throughput(**tp_stats)

        # M3: Validation rate from findings log
        findings_log = STATE_DIR / "findings_log.jsonl"
        vr_stats = self.compute_validation_rate_from_log(findings_log)
        total = sum(vr_stats[k] for k in
                    ["validated", "preliminary", "rejected", "novel", "incomplete"])
        if total > 0:
            results["m3"] = self.record_validation_rate(**vr_stats)

        # M4: Tool reuse from journal
        journal_path = STATE_DIR / "journal.jsonl"
        tool_stats = self.compute_tool_reuse_from_journal(journal_path)
        for tool_name, stats in tool_stats.items():
            if stats["eligible_heartbeats"] > 0:
                results[f"m4_{tool_name}"] = self.record_tool_reuse(
                    tool_name=tool_name, **stats)

        return results

    # -------------------------------------------------------------------
    # Reporting
    # -------------------------------------------------------------------

    def latest_metrics(self) -> dict:
        """
        Get the most recent entry for each metric.

        Returns:
            Dict of metric_name → latest entry (or None if no data).
        """
        result = {}
        for name, path in METRIC_FILES.items():
            result[name] = _read_latest(path)
        return result

    def trend(self, metric_name: str, n: int = 10) -> list[dict]:
        """
        Get the N most recent entries for a specific metric.

        Args:
            metric_name: Key from METRIC_FILES (e.g., "m1_classification_accuracy")
            n: Number of entries to return

        Returns:
            List of entries, most recent last.
        """
        path = METRIC_FILES.get(metric_name)
        if not path or not path.exists():
            return []

        entries = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries[-n:]

    def summary_for_briefing(self) -> str:
        """
        Compact metrics summary for agent briefing injection.

        Token-efficient format for DSV4-Flash context budget.
        """
        latest = self.latest_metrics()
        parts = ["Self-measurement:"]

        m1 = latest.get("m1_classification_accuracy")
        if m1:
            v = m1.get("values", {})
            parts.append(
                f"M1 holdout={v.get('holdout_accuracy', 0):.1%}"
            )

        m2 = latest.get("m2_throughput")
        if m2:
            v = m2.get("values", {})
            parts.append(
                f"M2 {v.get('daily_rate', 0):.1f}/day"
            )

        m3 = latest.get("m3_validation_rate")
        if m3:
            v = m3.get("values", {})
            parts.append(
                f"M3 {v.get('validation_rate', 0):.0%} validated"
            )

        if len(parts) == 1:
            return "Self-measurement: No metrics collected yet."

        return " | ".join(parts) + "."

    def full_report(self) -> str:
        """
        Generate a full-text metrics report.

        Suitable for weekly synthesis or dashboard display.
        """
        lines = [
            "# Self-Measurement Report",
            f"Generated: {_now_iso()[:19]}Z",
            "",
        ]

        latest = self.latest_metrics()

        # M1
        m1 = latest.get("m1_classification_accuracy")
        lines.append("## M1: Classification Accuracy")
        if m1:
            v = m1.get("values", {})
            c = m1.get("context", {})
            lines.extend([
                f"  Model: {c.get('model_version', '?')}",
                f"  Holdout accuracy: {v.get('holdout_accuracy', 0):.3f}",
                f"  Macro F1: {v.get('macro_f1', 0):.3f}",
                f"  Samples: {v.get('n_train', 0)} train, {v.get('n_holdout', 0)} holdout",
                f"  Top features: {', '.join(c.get('top_features', [])[:3])}",
            ])
        else:
            lines.append("  No classifier trained yet.")
        lines.append("")

        # M2
        m2 = latest.get("m2_throughput")
        lines.append("## M2: Analysis Throughput")
        if m2:
            v = m2.get("values", {})
            lines.extend([
                f"  Period: {m2.get('measurement_period', '?')}",
                f"  Tiles completed: {v.get('tiles_completed', 0)}",
                f"  Daily rate: {v.get('daily_rate', 0):.2f} tiles/day",
                f"  Total in system: {v.get('total_tiles_in_system', 0)}",
            ])
        else:
            lines.append("  No throughput data yet.")
        lines.append("")

        # M3
        m3 = latest.get("m3_validation_rate")
        lines.append("## M3: Finding Validation Rate")
        if m3:
            v = m3.get("values", {})
            lines.extend([
                f"  Period: {m3.get('measurement_period', '?')}",
                f"  Validation rate: {v.get('validation_rate', 0):.1%}",
                f"  Breakdown: {v.get('validated', 0)} validated, "
                f"{v.get('preliminary', 0)} preliminary, "
                f"{v.get('rejected', 0)} rejected, "
                f"{v.get('novel', 0)} novel",
            ])
        else:
            lines.append("  No validation data yet.")
        lines.append("")

        # M4
        lines.append("## M4: Tool Reuse Rate")
        m4_entries = self.trend("m4_tool_reuse", n=20)
        if m4_entries:
            # Group by tool
            by_tool: dict[str, dict] = {}
            for e in m4_entries:
                tool = e.get("values", {}).get("tool", "?")
                by_tool[tool] = e  # Latest per tool
            for tool, e in sorted(by_tool.items()):
                v = e.get("values", {})
                lines.append(
                    f"  {tool}: {v.get('reuse_rate', 0):.0%} "
                    f"({v.get('invocations', 0)}/{v.get('eligible_heartbeats', 0)} eligible)"
                )
        else:
            lines.append("  No tool reuse data yet.")
        lines.append("")

        # M5
        m5 = latest.get("m5_council_quality")
        lines.append("## M5: Council Decision Quality")
        if m5:
            v = m5.get("values", {})
            lines.extend([
                f"  Poll: {v.get('poll_id', '?')}",
                f"  Options: {v.get('num_options', 0)}",
                f"  Specificity: {v.get('specificity_score', 0):.1f}/5",
                f"  Evidence citations: {v.get('evidence_citations', 0)}",
            ])
        else:
            lines.append("  No council data yet (weekly assessment by Titus-expedition).")
        lines.append("")

        # M6
        m6 = latest.get("m6_baseline_comparison")
        lines.append("## M6: Multi-Agent vs. Single-Agent")
        if m6:
            v = m6.get("values", {})
            ma = v.get("multi_agent", {})
            sa = v.get("single_agent", {})
            adv = v.get("advantage", {})
            lines.extend([
                f"  Comparison: {v.get('comparison_id', '?')}",
                f"  Multi-agent: {ma.get('findings', 0)} findings, "
                f"{ma.get('validated', 0)} validated",
                f"  Single-agent: {sa.get('findings', 0)} findings, "
                f"{sa.get('validated', 0)} validated",
                f"  Finding advantage: {adv.get('finding_ratio', 0):+.0%}",
                f"  Validation advantage: {adv.get('validation_ratio', 0):+.0%}",
            ])
        else:
            lines.append("  No baseline comparison yet (monthly measurement).")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, entry: dict) -> None:
    """Append a single JSON line to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def _append_metric(metric_name: str, entry: dict) -> None:
    """Append an entry to a named metric file."""
    path = METRIC_FILES.get(metric_name)
    if path:
        _append_jsonl(path, entry)


def _read_latest(path: Path) -> Optional[dict]:
    """Read the latest entry from a JSONL file."""
    if not path.exists():
        return None
    last_line = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            last_line = line
    if last_line:
        try:
            return json.loads(last_line)
        except json.JSONDecodeError:
            return None
    return None


def _macro_f1(per_class: dict) -> float:
    """Compute macro F1 from per-class metrics dict."""
    f1_scores = [
        v.get("f1-score", 0.0)
        for k, v in per_class.items()
        if isinstance(v, dict) and "f1-score" in v
    ]
    return sum(f1_scores) / len(f1_scores) if f1_scores else 0.0


def _infer_tools_from_stage(stage: str) -> list[str]:
    """Infer which tools were likely used based on pipeline stage."""
    stage_tools = {
        "acquire": ["stac_search"],
        "analyze": ["spectral_indices", "tile_reader"],
        "validate": ["validation_pipeline"],
        "maintain": [],
        "synthesize": [],
    }
    return stage_tools.get(stage, [])


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------

def main():
    """CLI for metrics operations."""
    import argparse

    parser = argparse.ArgumentParser(
        description="NSE Self-Measurement Infrastructure",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("report", help="Generate full metrics report")
    sub.add_parser("summary", help="Brief metrics summary (for briefing)")
    sub.add_parser("aggregate", help="Run periodic aggregation (M2/M3/M4)")

    trend_p = sub.add_parser("trend", help="Show metric trend")
    trend_p.add_argument("metric", choices=list(METRIC_FILES.keys()),
                         help="Which metric to trend")
    trend_p.add_argument("-n", type=int, default=10,
                         help="Number of entries (default: 10)")

    args = parser.parse_args()
    mc = MetricsCollector()

    if args.command == "report":
        print(mc.full_report())
    elif args.command == "summary":
        print(mc.summary_for_briefing())
    elif args.command == "aggregate":
        results = mc.run_periodic_aggregation()
        if results:
            print(f"Aggregated {len(results)} metric(s):")
            for k in results:
                print(f"  - {k}")
        else:
            print("No metrics to aggregate (no data in state files).")
    elif args.command == "trend":
        entries = mc.trend(args.metric, n=args.n)
        if entries:
            for e in entries:
                ts = e.get("timestamp", "?")[:19]
                vals = json.dumps(e.get("values", {}), indent=None)
                print(f"[{ts}] {vals}")
        else:
            print(f"No entries for {args.metric}.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
