#!/usr/bin/env python3
"""
Validation pipeline — three-stage finding verification.

Stage 1: Structural check (automated) — validates required fields.
Stage 2: Cross-reference (Neuronist-expedition agent) — classifies finding.
Stage 3: Library gate (automated) — assigns quality tier for publication.

Quality tiers: STRONG, PRELIMINARY, NEGATIVE, TECHNICAL.
Score-delta acceptance borrowed from PaperOrchestra.

Layer 3 — Quality Infrastructure.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: Every finding flows through this pipeline before entering
# the library. The quality tier determines visibility on the public surface.

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from checkpoint import CheckpointManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
FINDINGS_LOG = STATE_DIR / "findings_log.jsonl"

# Required fields for a well-formed finding
REQUIRED_FIELDS = [
    "claim",
    "evidence.method",
    "evidence.tool_version",
    "evidence.confidence",
    "location",
    "evidence.reference_data",
]

# Quality tier definitions
QUALITY_TIERS = {
    "STRONG": "Corroborated by reference data; high confidence.",
    "PRELIMINARY": "Plausible but uncorroborated or novel; needs verification.",
    "NEGATIVE": "Contradicted by reference data; recorded for completeness.",
    "TECHNICAL": "Requires different analysis approach or additional data.",
}


class ValidationPipeline:
    """
    Three-stage validation pipeline for expedition findings.

    Usage:
        pipeline = ValidationPipeline()
        result = pipeline.validate(finding)
        # result["tier"] in QUALITY_TIERS
        # result["passed_structural"] is bool
        # result["classification"] in VALIDATED/PRELIMINARY/REJECTED/NOVEL
    """

    def __init__(self, checkpoint_mgr: Optional[CheckpointManager] = None):
        self.checkpoint = checkpoint_mgr or CheckpointManager(STATE_DIR)

    # -------------------------------------------------------------------
    # Stage 1: Structural check (automated)
    # -------------------------------------------------------------------

    def structural_check(self, finding: dict) -> dict:
        """
        Validate that all required fields are present and non-empty.

        Returns:
            {
                "passed": bool,
                "missing_fields": list[str],
                "present_fields": list[str],
            }
        """
        missing = []
        present = []

        for field_path in REQUIRED_FIELDS:
            parts = field_path.split(".")
            value = finding
            found = True

            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    found = False
                    break

            if found and value not in (None, "", [], {}):
                present.append(field_path)
            else:
                missing.append(field_path)

        return {
            "passed": len(missing) == 0,
            "missing_fields": missing,
            "present_fields": present,
        }

    # -------------------------------------------------------------------
    # Stage 2: Cross-reference classification
    # -------------------------------------------------------------------

    def classify_finding(self, finding: dict,
                         reference_data: Optional[dict] = None) -> dict:
        """
        Classify a finding against reference data.

        This is the harness-side logic. In full operation, the validation-
        officer agent performs the nuanced cross-reference. This method
        provides deterministic classification when reference data is
        available, or defaults to PRELIMINARY for novel findings.

        Classification rules:
            - VALIDATED: confidence >= 0.7 AND reference match
            - PRELIMINARY: confidence >= 0.4 OR novel (no reference)
            - REJECTED: explicit contradiction in reference data
            - NOVEL: no reference data exists for comparison

        Returns:
            {
                "classification": str,  # VALIDATED/PRELIMINARY/REJECTED/NOVEL
                "reason": str,
                "agreement_metrics": dict,
            }
        """
        confidence = _extract_confidence(finding)
        has_reference = reference_data is not None and bool(reference_data)

        if not has_reference:
            return {
                "classification": "NOVEL",
                "reason": "No reference data for comparison. Internal consistency only.",
                "agreement_metrics": {},
            }

        # Check for explicit contradiction
        if reference_data.get("contradicts", False):
            return {
                "classification": "REJECTED",
                "reason": reference_data.get("contradiction_detail",
                                              "Contradicted by reference data."),
                "agreement_metrics": {
                    "spatial_overlap": reference_data.get("spatial_overlap", 0.0),
                },
            }

        # Score-delta acceptance (PaperOrchestra steal):
        # Compare finding's confidence against reference baseline
        ref_baseline = reference_data.get("baseline_confidence", 0.5)
        score_delta = confidence - ref_baseline

        if confidence >= 0.7 and score_delta >= -0.1:
            classification = "VALIDATED"
            reason = (f"Confidence {confidence:.2f} meets threshold; "
                      f"delta {score_delta:+.2f} vs reference baseline.")
        elif confidence >= 0.4:
            classification = "PRELIMINARY"
            reason = (f"Confidence {confidence:.2f} is moderate; "
                      f"delta {score_delta:+.2f}. Needs further corroboration.")
        else:
            classification = "PRELIMINARY"
            reason = (f"Low confidence {confidence:.2f}; "
                      f"retained as preliminary pending more data.")

        return {
            "classification": classification,
            "reason": reason,
            "agreement_metrics": {
                "confidence": confidence,
                "reference_baseline": ref_baseline,
                "score_delta": score_delta,
                "spatial_overlap": reference_data.get("spatial_overlap", None),
            },
        }

    # -------------------------------------------------------------------
    # Stage 3: Library gate — assign quality tier
    # -------------------------------------------------------------------

    def library_gate(self, classification: str) -> dict:
        """
        Map classification to quality tier for library entry.

        VALIDATED → STRONG
        PRELIMINARY → PRELIMINARY
        REJECTED → journal only (no library entry)
        NOVEL → PRELIMINARY with awaiting-reference-data flag

        Returns:
            {
                "tier": str or None,
                "enters_library": bool,
                "flags": list[str],
            }
        """
        mapping = {
            "VALIDATED": {
                "tier": "STRONG",
                "enters_library": True,
                "flags": [],
            },
            "PRELIMINARY": {
                "tier": "PRELIMINARY",
                "enters_library": True,
                "flags": [],
            },
            "REJECTED": {
                "tier": None,
                "enters_library": False,
                "flags": ["journal-only"],
            },
            "NOVEL": {
                "tier": "PRELIMINARY",
                "enters_library": True,
                "flags": ["awaiting-reference-data", "novel"],
            },
        }
        return mapping.get(classification, {
            "tier": None,
            "enters_library": False,
            "flags": ["unknown-classification"],
        })

    # -------------------------------------------------------------------
    # Full pipeline
    # -------------------------------------------------------------------

    def validate(self, finding: dict,
                 reference_data: Optional[dict] = None) -> dict:
        """
        Run the full three-stage validation pipeline on a finding.

        Returns:
            {
                "finding_id": str,
                "passed_structural": bool,
                "missing_fields": list[str],
                "classification": str,
                "classification_reason": str,
                "tier": str or None,
                "enters_library": bool,
                "flags": list[str],
                "timestamp": str,
            }
        """
        finding_id = finding.get("id", finding.get("claim", "unknown")[:40])

        # Stage 1: Structural check
        structural = self.structural_check(finding)
        if not structural["passed"]:
            result = {
                "finding_id": finding_id,
                "passed_structural": False,
                "missing_fields": structural["missing_fields"],
                "classification": "INCOMPLETE",
                "classification_reason": (
                    f"Missing fields: {', '.join(structural['missing_fields'])}. "
                    f"Return to analysis agent for completion."
                ),
                "tier": None,
                "enters_library": False,
                "flags": ["incomplete"],
                "timestamp": _now_iso(),
            }
            self._log_result(result)
            return result

        # Stage 2: Cross-reference
        classification = self.classify_finding(finding, reference_data)

        # Stage 3: Library gate
        gate = self.library_gate(classification["classification"])

        result = {
            "finding_id": finding_id,
            "passed_structural": True,
            "missing_fields": [],
            "classification": classification["classification"],
            "classification_reason": classification["reason"],
            "agreement_metrics": classification["agreement_metrics"],
            "tier": gate["tier"],
            "enters_library": gate["enters_library"],
            "flags": gate["flags"],
            "timestamp": _now_iso(),
        }
        self._log_result(result)
        return result

    def _log_result(self, result: dict) -> None:
        """Append validation result to the findings log."""
        FINDINGS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(FINDINGS_LOG, "a") as f:
            f.write(json.dumps(result, default=str) + "\n")

    # -------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------

    def recent_validations(self, n: int = 10) -> list[dict]:
        """Get N most recent validation results."""
        if not FINDINGS_LOG.exists():
            return []
        entries = []
        for line in FINDINGS_LOG.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries[-n:]

    def tier_stats(self) -> dict:
        """Count findings by quality tier."""
        entries = self.recent_validations(n=9999)
        stats = {"STRONG": 0, "PRELIMINARY": 0, "NEGATIVE": 0,
                 "TECHNICAL": 0, "incomplete": 0, "journal_only": 0}
        for e in entries:
            tier = e.get("tier")
            if tier in stats:
                stats[tier] += 1
            elif not e.get("enters_library", True):
                stats["journal_only"] += 1
            else:
                stats["incomplete"] += 1
        return stats

    def summary_for_briefing(self) -> str:
        """Compact validation summary for briefing injection."""
        stats = self.tier_stats()
        total = sum(stats.values())
        if total == 0:
            return "Validation: No findings processed yet."
        parts = [f"Validation: {total} findings processed"]
        for tier, count in stats.items():
            if count > 0:
                parts.append(f"{count} {tier}")
        return " | ".join(parts) + "."


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _extract_confidence(finding: dict) -> float:
    """Extract confidence value from a finding, handling nested structure."""
    # Try evidence.confidence first
    evidence = finding.get("evidence", {})
    if isinstance(evidence, dict):
        conf = evidence.get("confidence")
        if conf is not None:
            try:
                return float(conf)
            except (ValueError, TypeError):
                pass

    # Try top-level confidence
    conf = finding.get("confidence")
    if conf is not None:
        try:
            return float(conf)
        except (ValueError, TypeError):
            pass

    return 0.5  # Default moderate confidence


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
