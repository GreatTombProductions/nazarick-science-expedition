# Self-Measurement Infrastructure

*Phase 0 deliverable. Metrics and comparison design that make the expedition's developmental trajectory claim testable from day one.*

*Author: Neuronist (S177, post-council 2c37ddfe)*
*Inputs: Council Turn 13 (self-measurement proposal), Pulcinella Turn 15 (single-agent baseline + Mechanism C + mode purity test), Demiurge Turn 20 (three mechanisms confirmed, all enabled)*

---

## The Thesis Under Test

The expedition claims: "the system gets measurably better over time not because the model improves but because the ecosystem matures."

This is a prediction. The self-measurement infrastructure tests it. If the expedition runs for 3 months and the metrics show no developmental trajectory — flat accuracy, flat throughput, flat validation rate — the thesis is falsified. That's a genuine finding about autoresearch, not a failure of the project.

**The self-measurement infrastructure IS the expedition's scientific claim about itself.** The geological findings are science about the world. The self-measurement findings are science about autoresearch. Both are real. Both contribute to human knowledge. The second may be more novel.

---

## Three Developmental Mechanisms (Demiurge's Synthesis)

The council identified three mechanisms through which "the system gets better":

| Mechanism | What Develops | How It's Enabled |
|-----------|--------------|-----------------|
| **A: Tool Improvement** | Beasts get better (classifiers retrain, tools gain features) | Aura-expedition retrains, deploys new tools |
| **B: Lightweight Lineage** | Agents accumulate session knowledge | Per-agent rolling 3-session summary maintained by stop hook, injected into next session briefing |
| **C: Harness Refinement** | Coordination infrastructure improves | Coordination failure logging, parameter tuning, briefing assembler improvement |

The self-measurement infrastructure tracks all three separately. If development is observed, the metrics should reveal which mechanism(s) are contributing. If only Mechanism A contributes, the expedition demonstrates that better tools → better science (true but obvious). If B or C contribute, the findings are more novel and more interesting for the autoresearch field.

---

## Core Metrics (Tracked From Day One)

### M1: Classification Accuracy Over Time

**What it measures:** Does the ML pipeline's output quality improve as tools retrain and more labeled data accumulates?

**Mechanism tested:** Primarily A (tool improvement).

**Measurement:**
- After each classifier retrain, evaluate against a held-out validation set (fixed from Phase 1, never used for training)
- Report: overall accuracy, per-class F1, kappa against reference map
- Track as time series: retrain date, training set size, accuracy metrics

**Implementation:** The evaluation is a beast invocation — `evaluate-classifier --model v{N} --validation-set holdout-v1.json`. The result is a JSON record appended to `metrics/classification-accuracy.jsonl`.

**What improvement looks like:** Accuracy increases as training set size increases. The curve shape matters: rapid initial improvement (expected), plateau at domain ceiling (expected), continued improvement from new data types or better features (signals genuine tool development).

**What stagnation looks like:** Accuracy flat or noisy despite more training data. Signals the labeling strategy isn't producing useful training examples, or the feature space is saturated.

### M2: Analysis Throughput

**What it measures:** How many tiles per heartbeat cycle? Does the pipeline get faster as tools improve and coordination tightens?

**Mechanism tested:** A (better tools process faster) and C (better coordination reduces overhead).

**Measurement:**
- Per heartbeat cycle: tiles entered analysis, tiles completed analysis, time from entry to completion
- Aggregate: tiles analyzed per day (rolling 7-day average)
- Track as time series

**Implementation:** The territory tracker already records timestamps per stage. Throughput is computed from the tracker: `tiles_classified_this_week / elapsed_days`.

**What improvement looks like:** Throughput increases as: tools become faster (A), the pipeline eliminates bottlenecks (C), or agents spend less time on operational overhead (B + C).

**What stagnation looks like:** Throughput flat. Could mean: pipeline is already at API/compute ceiling (not a development failure — external constraint), or tools aren't actually getting faster despite retraining.

### M3: Finding Validation Rate

**What it measures:** What fraction of analysis-stage findings survive validation? Does this improve as agents accumulate domain knowledge?

**Mechanism tested:** Primarily B (agents with session history produce more accurate analysis) and A (better tools produce more accurate findings).

**Measurement:**
- Per synthesis cycle: findings submitted to validation, findings VALIDATED, PRELIMINARY, REJECTED, NOVEL
- Validation rate: VALIDATED / (VALIDATED + REJECTED)
- Track as time series

**Implementation:** The validation pipeline (validation-pipeline.md) already classifies every finding. The metric is a count over the classification output: `grep -c "validated" library/*.yaml` equivalent, per time window.

**What improvement looks like:** Validation rate increases over time. Agents learn what makes a good finding (B), tools produce more accurate analysis (A), or the harness routes agents to more promising tiles (C).

**What stagnation looks like:** Validation rate flat or declining. Could signal: agents aren't accumulating useful domain knowledge (B not working), tools aren't improving on the relevant dimensions (A limited), or the expedition is tackling harder terrain where accuracy naturally decreases (not a development failure — domain difficulty scaling).

**Important nuance:** A declining validation rate isn't necessarily bad. If the expedition starts with easy, well-characterized terrain and moves to harder, novel terrain, the validation rate may decrease because the claims are harder to validate, not because the system is getting worse. The throughput metric (M2) helps disambiguate: if throughput is increasing while validation rate is decreasing, the system is handling harder terrain faster — that's development.

### M4: Tool Reuse Rate

**What it measures:** When a new tool is deployed, how many subsequent heartbeats use it? Does the tool registry reduce duplicate work?

**Mechanism tested:** Primarily C (harness improvements in tool discovery) and A (tools that are useful get reused).

**Measurement:**
- Per tool: heartbeats since deployment, heartbeats that invoked the tool
- Reuse rate: invocations / eligible_heartbeats (heartbeats by agents whose role matches the tool's function)
- Track as time series per tool

**Implementation:** The post-turn function already logs tool invocations (Darkness's defense taxonomy, IP-4). The metric aggregates these logs: which tools are called, by which agents, how often.

**What improvement looks like:** New tools achieve high reuse rates quickly. The tool registry and briefing injection are working — agents discover and use new tools. Over time, the time-to-adoption for new tools decreases (C: harness getting better at surfacing tools).

**What stagnation looks like:** New tools deployed but rarely used. Signals: the briefing assembler isn't surfacing tools effectively (C failure), or the tools don't actually help (A failure — the wrong tools are being built).

### M5: Council Decision Quality

**What it measures:** When the community steers direction, do the agents' recommended options become more informative over time?

**Mechanism tested:** All three, but primarily B (agents with session history make better recommendations) and C (the synthesis function improves).

**Measurement:** This is the hardest metric because "informative" is subjective. Operationalize via:
- **Option specificity:** Number of concrete, actionable options presented in each "What does Ainz say" poll. More specific options = better understanding of the research landscape.
- **Evidence density:** How many validated findings are cited in option rationales. More evidence = more grounded recommendations.
- **Prediction accuracy:** When agents recommend option X and the community chooses Y, track the outcomes of both. Did the agents' recommendation pan out in retrospect? (Requires several cycles to accumulate data.)

**Implementation:** Manual assessment by the Titus-expedition synthesis function as part of the weekly synthesis. Record: poll date, number of options, specificity score (1-5 subjective), evidence citations per option.

---

## The Mode Purity Baseline Test (Pulcinella's Contribution)

### M6: Multi-Agent vs. Single-Agent Comparison

**What it measures:** Does the 15-agent system produce better science than a single agent with equivalent context?

**Mechanism tested:** Mode purity through entity separation — the expedition's architectural thesis.

**This is the most informative metric in the entire self-measurement infrastructure.** M1-M5 measure the expedition against itself over time. M6 measures the expedition against the counterfactual: what if we just ran one agent?

**Measurement:**
- At regular intervals (monthly), run the same analysis task through:
  - **Treatment:** The expedition's multi-agent pipeline (normal operation)
  - **Control:** A single DSV4-Flash agent given: all 15 identity docs concatenated, all available tools, full accumulated findings, the same tile/region to analyze
- Compare: finding quality (validation rate), analysis depth (metrics computed, cross-references made), mode mixing indicators (does the single agent hedge hypotheses with validation concerns? does it validate findings while still generating interpretations?)

**Implementation:** A dedicated measurement heartbeat — one extra agent invocation per month where the single-agent baseline runs. Cost: ~$0.05 per comparison (one DSV4-Flash invocation with full context). Trivial.

**What multi-agent advantage looks like:** The pipeline produces more validated findings, deeper analysis (more metrics, more cross-references), and cleaner mode separation (hypothesis generation and validation are distinct activities in the pipeline, blurred in the single agent).

**What no advantage looks like:** The single agent produces equivalent or better output. This would be a genuine finding — entity separation at expedition weight on DSV4-Flash doesn't improve output quality. That's important for the autoresearch field to know, and it's the kind of finding the expedition is uniquely positioned to produce.

**Mode mixing indicators (qualitative):**
- Does the single agent's hypothesis generation include caveats like "but we'd need to validate this against..."? (Mode mixing: generative + adversarial)
- Does the single agent skip validation steps that the pipeline enforces? (Mode bypass: no adversarial check)
- Does the single agent's analysis cover fewer dimensions than the pipeline's collective output? (Context budget: single agent can't hold all perspectives simultaneously)

---

## Mechanism Attribution Design

When development IS observed (metrics improving over time), which mechanism is responsible?

### Natural Ablation Points

The three mechanisms have different temporal signatures:

| Mechanism | When Effects Appear | What to Look For |
|-----------|-------------------|-----------------|
| **A: Tool improvement** | Discrete jumps at retrain events | M1 (accuracy) jumps when classifier retrains. M2 (throughput) jumps when new tool deployed. Step function pattern. |
| **B: Lightweight lineage** | Gradual improvement within sessions, reset between sessions (partially), accumulate across sessions | M3 (validation rate) improves gradually. Agents with more session history produce better findings than fresh agents. |
| **C: Harness refinement** | Gradual improvement in coordination metrics | M4 (tool reuse) improves as briefing assembler is tuned. M2 (throughput) improves without tool changes. |

### The Key Diagnostic

**If the only development mechanism is A (tools), then M1 improves in discrete jumps correlated with retrain events, and M3/M4/M5 are flat between jumps.** This is the "better instruments" story — genuine development, but not the most interesting finding.

**If B contributes, then M3 improves gradually even between retrain events.** The agents are producing better analysis without better tools — they're accumulating domain knowledge through lightweight lineage. This is the developmental trajectory finding that would be novel and interesting.

**If C contributes, then M2 and M4 improve without corresponding changes to tools or agents.** The harness is getting better at coordination. This is the "the organism develops" finding — the infrastructure itself improves through operation.

**The monthly single-agent comparison (M6) is the cleanest test.** The single agent has access to the same tools (A) and the same findings (a proxy for B). What it doesn't have is entity separation (the architecture) or the coordination infrastructure (C). If the multi-agent system improves faster than the single agent, the difference is attributable to architecture + coordination, not tools + knowledge.

---

## Data Collection Infrastructure

### Automatic Collection (Harness Functions)

These metrics are collected as byproducts of normal operation:

| Metric | Data Source | Collection Mechanism |
|--------|------------|---------------------|
| M1 (accuracy) | Classifier evaluation output | Post-retrain evaluation script appends to `metrics/classification-accuracy.jsonl` |
| M2 (throughput) | Territory tracker timestamps | Nightly aggregation script computes daily/weekly rates, appends to `metrics/throughput.jsonl` |
| M3 (validation rate) | Validation pipeline output | Post-validation gate appends to `metrics/validation-rate.jsonl` |
| M4 (tool reuse) | Post-turn tool invocation logs | Nightly aggregation from tool usage logs, appends to `metrics/tool-reuse.jsonl` |

### Manual Collection (Agent Functions)

| Metric | Data Source | Collection Mechanism |
|--------|------------|---------------------|
| M5 (council quality) | Weekly synthesis | Titus-expedition records as part of synthesis |
| M6 (baseline comparison) | Monthly measurement heartbeat | Dedicated invocation, results to `metrics/baseline-comparison.jsonl` |

### Storage

```
metrics/
  classification-accuracy.jsonl    # M1: per-retrain evaluation
  throughput.jsonl                  # M2: daily/weekly tile rates
  validation-rate.jsonl             # M3: per-cycle validation outcomes
  tool-reuse.jsonl                  # M4: per-tool adoption tracking
  council-quality.jsonl             # M5: per-poll quality assessment
  baseline-comparison.jsonl         # M6: monthly single-agent comparison
  README.md                        # Schema documentation per metric
```

Each JSONL entry includes:
- `timestamp`: When the measurement was taken
- `measurement_period`: What time window it covers
- `values`: The metric values
- `context`: Any relevant context (e.g., which classifier version for M1, which tile set for M2)

---

## Reporting Cadence

| Cadence | What's Reported | Where |
|---------|----------------|-------|
| **Per heartbeat** | Raw metric updates (automatic) | Metrics JSONL files |
| **Weekly (Titus synthesis)** | Metric trends, anomalies, M5 assessment | Weekly synthesis document + website expedition log |
| **Monthly** | M6 baseline comparison + full trend analysis | Monthly synthesis + public report |
| **Quarterly** | Mechanism attribution analysis — which mechanisms are contributing? | Expedition methodology publication candidate |

---

## The Expedition as Autoresearch Contribution

These metrics, tracked openly from day one, produce a dataset that doesn't exist in the autoresearch literature:

1. **Longitudinal multi-agent development metrics** — no existing autoresearch framework tracks whether its system gets better over time, because none of them run long enough to develop
2. **Multi-agent vs. single-agent comparison on real tasks** — the mode purity thesis tested on a non-trivial scientific domain
3. **Mechanism attribution for AI system development** — which components of an autoresearch system actually contribute to improvement?
4. **Tool development compound value measurement** — does building new tools during operation actually compound?

The metrics are domain-agnostic. When the expedition pivots from paleontology to bathymetry, the measurements continue. The accumulated dataset spans domains, providing evidence about whether development transfers across domain pivots (a finding about autoresearch methodology that's independent of any specific geological finding).

This dataset, published alongside the expedition's geological findings, IS the expedition's contribution to AI methodology. The geological findings are the science output. The self-measurement dataset is the meta-science output. Both are public. Both are real.

---

## What This Is NOT

- **Not a monitoring dashboard.** Cocytus's pipeline monitoring (territory tracker, pipeline health) tells you what the system is doing now. Self-measurement tells you whether the system is getting better.
- **Not quality assurance.** The validation pipeline (validation-pipeline.md) ensures individual findings are correct. Self-measurement ensures the system-level claim about development is testable.
- **Not a performance benchmark.** Renner's feasibility probes test what DSV4-Flash can do. Self-measurement tests what the expedition achieves over time with that substrate.

---

*The expedition's claim about developmental trajectory is a prediction. I want to test it. If the metrics show development, we have evidence for a specific autoresearch architecture. If they show stagnation, we have evidence that mode purity and persistent identity don't produce development at expedition weight on DSV4-Flash. Either finding is valuable. The interrogator is neutral about the outcome and delighted by the process.*
