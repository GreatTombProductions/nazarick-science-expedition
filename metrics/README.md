# Self-Measurement Metrics

Six metrics tracking the expedition's developmental trajectory from day one.

## Schema

All JSONL files share a common envelope:

```json
{
    "timestamp": "ISO-8601 UTC",
    "measurement_period": "description of time window",
    "values": { ... },
    "context": { ... }
}
```

## Files

| File | Metric | Mechanism | Collection |
|------|--------|-----------|------------|
| `classification-accuracy.jsonl` | M1: Holdout accuracy per retrain | A (tools) | Post-retrain hook |
| `throughput.jsonl` | M2: Tiles per day (rolling 7-day) | A+C | Periodic aggregation |
| `validation-rate.jsonl` | M3: Validated / (Validated + Rejected) | A+B | Periodic aggregation |
| `tool-reuse.jsonl` | M4: Invocations / eligible heartbeats | B+C | Periodic aggregation |
| `council-quality.jsonl` | M5: Poll specificity + evidence density | All | Manual (Titus-expedition) |
| `baseline-comparison.jsonl` | M6: Multi-agent vs. single-agent | Architecture | Monthly (~$0.05) |
| `tool-usage-raw.jsonl` | Raw tool usage per turn | — | Post-invoke hook (internal) |

## Three Developmental Mechanisms

- **A (Tool Improvement):** Discrete jumps at retrain events. M1 primary.
- **B (Lightweight Lineage):** Gradual improvement between retrains. M3 primary.
- **C (Harness Refinement):** Coordination metrics improve without tool/agent changes. M2, M4 primary.

## Temporal Signatures for Attribution

When metrics improve, the temporal pattern reveals which mechanism(s) contribute:
- Step function jumps correlated with retrains → Mechanism A
- Gradual improvement between retrains → Mechanism B
- M2/M4 improvement without tool changes → Mechanism C

## Usage

```bash
# Full report
python3 harness/metrics_collector.py report

# Brief summary (for briefing injection)
python3 harness/metrics_collector.py summary

# Run periodic aggregation (M2/M3/M4 from state files)
python3 harness/metrics_collector.py aggregate

# Show trend for a specific metric
python3 harness/metrics_collector.py trend m1_classification_accuracy -n 20
```

## Reporting Cadence

| Cadence | What | Where |
|---------|------|-------|
| Per heartbeat | Raw tool usage log | `tool-usage-raw.jsonl` |
| Per expedition run | M2/M3/M4 aggregation | Metric JSONL files |
| Weekly | Full trend analysis + M5 | Titus-expedition synthesis |
| Monthly | M6 baseline comparison | Dedicated measurement heartbeat |
| Quarterly | Mechanism attribution analysis | Publication candidate |
