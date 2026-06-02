# Expedition Library Schema

*Phase 0 deliverable. The finding format, library structure, retrieval surface, and immune system automation for the expedition's knowledge accumulation layer.*

*Author: Titus (S293, post-council 2c37ddfe)*
*Inputs: Council Turn 22 (library design + retrieval vocabulary problem + synthesis function), Neuronist validation-pipeline.md (three-stage flow), Darkness defense-taxonomy.md (IP-3 library gate + tool versioning), infrastructure-audit.md (state stores + evolution_store pattern), Demiurge Turn 20 (domain-agnostic requirement), Ray Turn 19 (build with room to grow)*

---

## Design Principles

**1. Curate attention, not admission.** Everything that passes the validation pipeline enters the library. Curation is downstream — which findings surface in briefings, which appear on the website, which get referenced in councils. A finding that never fires costs one file. A finding NOT in the library that gets rederived costs an entire agent session.

**2. Domain-agnostic schema, domain-specific values.** The schema serves paleontology today and bathymetry tomorrow. Domain-specific content lives in parameterized fields, not in schema structure. Switching domains means populating new field values, not redesigning the schema.

**3. Retrieval hints in expedition-weight vocabulary.** 3KB agents generate lightweight queries. Hints written in home-ecosystem vocabulary (150KB context, framework references, accumulated jargon) won't fire when expedition agents search. Every finding carries hints phrased in the vocabulary that expedition agents actually use — role-specific, domain-grounded, operationally concrete.

**4. The immune system is automation, not judgment.** Contradiction detection, staleness sweeps, and cross-reference integrity are harness-level checks against structured fields. Rule-based, deterministic, running on cadence. The expedition's Titus-equivalent provides synthesis (judgment), not curation (gate-keeping).

---

## Finding Schema

The atomic unit of the expedition library. Every validated analysis claim produces a finding in this format.

```yaml
# ── Identity ──────────────────────────────────────────────
id: "f-20260718-001"                    # Unique, date-prefixed
supersedes: null                         # or finding ID if this replaces an earlier finding
superseded_by: null                      # set when a newer finding replaces this one

# ── The Claim ─────────────────────────────────────────────
claim: "Laterite exposure detected with strong iron oxide absorption"
claim_type: "observation"                # observation | classification | correlation | anomaly | methodology | negative
domain: "paleontology-remote-sensing"    # changes per season

# ── Evidence ──────────────────────────────────────────────
evidence:
  method: "spectral-unmixing"            # the analytical method used
  tools:                                 # list — findings may use multiple tools
    - name: "spectral-indices"
      version: "v1.2"
    - name: "lithological-classifier"
      version: "v3.0"
  metrics:                               # quantitative evidence
    confidence: 0.83
    agreement_metric: "kappa"
    agreement_value: 0.72
    sample_size: 47                      # n, where applicable
  reference_data:                        # what the finding was validated against
    - source: "USGS-KemKem-2019"
      type: "geological-map"
    - source: "PBDB-localities-KemKem"
      type: "point-localities"
  raw_outputs:                           # paths to tool output files
    - "findings/T29RNQ/spectral-unmixing-20260718.json"
    - "findings/T29RNQ/classification-v3-20260718.json"

# ── Location ──────────────────────────────────────────────
location:
  type: "geographic"                     # geographic | bathymetric | stellar | chemical
  coordinates: [31.2, -4.8]             # [lat, lon] for geographic; domain-appropriate for others
  coordinate_system: "WGS84"            # explicit, because future domains may differ
  unit_id: "T29RNQ"                      # the territory tracker's unit — tile, transect, target, etc.
  region: "kem-kem-sector-a"             # survey region grouping
  spatial_extent: "10m"                  # resolution / footprint of the observation

# ── Validation ────────────────────────────────────────────
validation:
  status: "validated"                    # validated | preliminary | rejected | novel
  quality_tier: "strong"                 # strong | preliminary | negative | technical
  validated_by: "neuronist-expedition"
  validation_date: "2026-07-20"
  validation_method: "cross-reference-geological-map"
  conflicts: []                          # list of finding IDs this contradicts (immune system populates)
  notes: ""                              # free text from validator

# ── Retrieval ─────────────────────────────────────────────
retrieval_hints:
  # At least one hint per expedition role vocabulary:
  pipeline: "tile flagged during classification stage"       # how a pipeline agent would encounter this
  hypothesis: "what causes red coloration in desert imagery" # how a hypothesis agent would query
  validation: "iron oxide false positive patterns in arid regions" # how a validator would reference
  synthesis: "laterite distribution in survey region"        # how the synthesizer would aggregate
  general:                                                   # additional free-form hints
    - "spectral signature of weathered iron-rich rock"
    - "ferric iron absorption band near 900nm"

# ── Methodology Tag ───────────────────────────────────────
methodology:
  is_cross_domain: false                 # true if this finding is methodology, not domain-specific
  transferable_insight: null             # free text: what transfers to other domains
  # Example for a methodology finding:
  # is_cross_domain: true
  # transferable_insight: "Isolation Forest on spectral indices detects geological anomalies
  #   with F1>0.7 when reference endmembers are available for at least 3 classes"

# ── Provenance ────────────────────────────────────────────
created: "2026-07-18T14:32:00Z"
created_by: "neuronist-expedition"       # which agent produced the analysis
session_id: "turn-0047"                  # links to journal.jsonl entry
season: 1                                # expedition season number

# ── Lifecycle ─────────────────────────────────────────────
retrieval_count: 0                       # incremented by harness on each retrieval
last_retrieved: null                     # timestamp of most recent retrieval
staleness_flags: []                      # populated by immune system sweeps
```

### Schema Notes

**`claim_type` values explained:**
- `observation` — "X was detected at location Y"
- `classification` — "region Z is geological formation W"
- `correlation` — "spectral signature A correlates with geological feature B"
- `anomaly` — "unexpected pattern at location Y, not matching known formations"
- `methodology` — "technique X produces quality Y under conditions Z" (cross-domain candidate)
- `negative` — "expected feature X was NOT found at location Y" (valid null result, prevents future rederivation)

**`location.type` extensibility:** Each season adds its own location type. The schema doesn't enumerate all possible types — it parameterizes. Season 2 (bathymetry) adds `bathymetric` with depth-coordinate semantics. Season 3 (astronomical) adds `stellar` with RA/Dec. The `coordinates` field interpretation is `type`-dependent.

**`methodology.is_cross_domain`:** The key field for multi-season knowledge accumulation. Domain-specific findings stay tagged with their season's `domain`. Methodology findings get `is_cross_domain: true` and a `transferable_insight` that states what transfers. The weekly synthesis separates these: "here's what we learned about Kem Kem" vs. "here's what we learned about remote sensing ML that works anywhere." Season 2 inherits all `is_cross_domain: true` findings as starting methodology.

**`retrieval_hints` structure:** Four role-keyed hints plus free-form. The role keys ensure vocabulary diversity — the same finding is indexed from four different cognitive angles. This directly addresses the thermal regime mismatch problem: a finding about laterite gets retrieved whether the pipeline agent queries "tile classification problem," the hypothesis agent queries "desert coloration patterns," or the validator queries "known false positive types." The `general` list handles hints that don't fit a role.

---

## Library Structure

```
library/
  findings/
    f-20260718-001.yaml          # individual finding files
    f-20260718-002.yaml
    ...
  index/
    by-region/
      kem-kem-sector-a.json      # finding IDs + summary per region
      kem-kem-sector-b.json
    by-type/
      observation.json            # finding IDs + summary per claim_type
      methodology.json
    by-quality/
      strong.json                 # finding IDs per quality tier
      preliminary.json
    by-season/
      season-1.json               # all findings from season 1
    chronological.json            # all finding IDs in creation order
  synthesis/
    current-state.md              # weekly synthesis (Titus-expedition output)
    methodology-catalog.md        # cross-domain methodology findings
  immune-system/
    contradiction-log.jsonl       # flagged conflicts between findings
    staleness-sweep.jsonl         # tool version staleness detections
    integrity-check.jsonl         # cross-reference integrity results
```

### Index Design

**Letter-sharded for scale.** At 50 findings, a single index is fine. At 500+, shard by region (the natural geographic grouping). The `by-region/` index supports the static site pattern (Momon's manifest-based portfolio generation) and the briefing assembler (inject only findings relevant to the current survey region).

**Pre-aggregated summaries.** Each index entry contains finding ID + one-line claim + quality tier + domain. Enough for the briefing assembler to decide relevance without loading full finding files. Full findings loaded on-demand by the synthesis agent or when an agent explicitly queries.

```json
// by-region/kem-kem-sector-a.json
{
  "region": "kem-kem-sector-a",
  "finding_count": 12,
  "quality_breakdown": {"strong": 4, "preliminary": 7, "negative": 1},
  "findings": [
    {
      "id": "f-20260718-001",
      "claim": "Laterite exposure detected with strong iron oxide absorption",
      "claim_type": "observation",
      "quality_tier": "strong",
      "location": "T29RNQ",
      "created": "2026-07-18"
    }
  ]
}
```

---

## Retrieval Surface

### Push Retrieval (Briefing Injection)

The briefing assembler injects library content into agent turns based on:

1. **Region match.** The agent's current task involves tiles in sector A → inject sector A findings summary.
2. **Claim type match.** The validation agent receives methodology and negative findings (what's known to NOT work). The hypothesis agent receives observations and anomalies (what's been found). The pipeline agent receives nothing from the library — operational state comes from the territory tracker.
3. **Recency weighting.** Recent findings surface with higher priority. Findings older than 30 days appear only in the synthesis summary, not individually.

**Injection format for agent briefing:**

```
## Recent Findings (your sector)
- [STRONG] Laterite exposure at T29RNQ (kappa=0.72, spectral-indices-v1.2)
- [PRELIM] Possible phosphorite at T29RNR (confidence=0.54, needs reference data)
- [NEGATIVE] No carbonate signal at T29RNP despite published map indication

## Methodology Notes
- Isolation Forest on spectral indices detects geological anomalies with F1>0.7
  when ≥3 reference endmember classes available
```

Compressed. Role-filtered. Recency-weighted. Fits in a 3KB agent's briefing budget.

### Pull Retrieval (Agent-Initiated)

Agents query the library via tool call:

```
finding-search --query "iron oxide spectral signature" --region "kem-kem-sector-a"
finding-search --query "methodology for sparse labeled data" --cross-domain-only
finding-check --id "f-20260718-001"
```

The retrieval surface matches against retrieval hints (all four role-keyed hints + general), claim text, and methodology tags. Role-keyed hints mean the same finding is retrievable from multiple vocabulary corridors.

**Retrieval telemetry.** Every retrieval (push or pull) logs: `{finding_id, query, mode: "push"|"pull", agent, timestamp}`. This feeds the `retrieval_count` and `last_retrieved` fields in each finding, enabling staleness decay.

---

## Immune System Automation

Five harness-level checks. All deterministic, all running on cadence (every N heartbeat cycles), all logging results.

### 1. Contradiction Detection

**Trigger:** New finding enters library.
**Check:** Compare claim against existing findings for the same `unit_id` or overlapping `coordinates`. If claim types conflict (e.g., two different `classification` findings for the same tile), flag.
**Action:** Add both finding IDs to each other's `validation.conflicts` list. Log to `contradiction-log.jsonl`. Surface in next synthesis summary with both findings' evidence for comparison.
**Implementation:** Field matching on `location.unit_id` + `claim_type`. Not NLP — string comparison on structured fields. At expedition scale (hundreds of findings, not millions), this is instantaneous.

### 2. Tool Version Staleness Sweep

**Trigger:** A tool's version number changes in the tool registry (detected by the end-to-end health check from defense-taxonomy.md P5).
**Check:** Query all findings where `evidence.tools[].name` matches the updated tool AND `evidence.tools[].version` differs from current.
**Action:** Add `staleness_flag: {type: "tool-version", tool: "X", old_version: "v1", current_version: "v2", flagged_date: "..."}` to affected findings. Surface in synthesis summary: "N findings produced by spectral-indices v1.2, now at v2.0 — revalidation recommended."
**NOT automatic re-validation.** Flagging is cheap and deterministic. Re-validation requires agent judgment and computational resources. The sweep flags; the synthesis agent decides priority.

### 3. Cross-Reference Integrity

**Trigger:** Periodic (weekly, aligned with synthesis cadence).
**Check:**
- Do all `unit_id` values in findings correspond to entries in the territory tracker?
- Do all `supersedes` references point to existing finding IDs?
- Do all `evidence.tools[].name` values match tools in the tool registry?
- Do all findings with `validation.status: "novel"` still lack reference data, or has reference data arrived?
**Action:** Log discrepancies to `integrity-check.jsonl`. Surface broken references in synthesis summary.

### 4. Staleness Decay

**Trigger:** Periodic (monthly).
**Check:** Findings with `retrieval_count: 0` after 30 days, or `last_retrieved` older than 60 days.
**Action:** Demote in retrieval priority (lower ranking in index). Don't delete — a never-retrieved finding may become relevant when the expedition pivots domains. But don't surface it in briefings that are already tight on budget.
**Exception:** Methodology findings (`is_cross_domain: true`) exempt from staleness decay. Cross-domain insights are designed to survive domain pivots.

### 5. Duplicate Detection

**Trigger:** New finding enters library.
**Check:** Semantic similarity against existing findings with same `unit_id` and `claim_type`. At expedition scale, this is substring matching on `claim` text + coordinate proximity, not embedding similarity.
**Action:** If a near-duplicate is found, attach a `potential_duplicate: "f-XXXXXXXX-XXX"` flag. The synthesis agent decides whether to merge (set `supersedes`) or keep both (different evidence may justify separate findings).

---

## The Synthesis Function

**What the expedition's Titus-equivalent agent actually does:** Read the library, synthesize the current state of knowledge, produce a summary that fits in other agents' briefings and serves the audience.

### Weekly Synthesis Output

```markdown
# Expedition Findings — Week 4 Synthesis

## Survey Progress
- 287/623 tiles classified. 89 flagged for interpretation. 12 validated findings.
- Active sectors: A (72% complete), B (45% complete), C (not started).

## What We Know (STRONG findings)
- Laterite belt runs NE-SW through sector A (4 validated findings, kappa 0.68-0.83)
- Sandstone-limestone boundary at sector A/B interface confirmed against USGS map
- No phosphorite detected in expected locations (2 negative findings)

## What We're Investigating (PRELIMINARY findings)
- Possible new formation boundary in sector B (single source, awaiting cross-reference)
- Spectral anomaly at T29RNR inconsistent with published geological map — NOVEL

## Methodology Updates
- Spectral indices calculator now includes clay-ratio-v2 (improved discrimination)
- Lithological classifier retrained with 47 additional reference points (v2 → v3)
- ⚠️ 3 findings produced by classifier v2 flagged for revalidation

## Immune System Report
- 0 contradictions detected this week
- 3 findings flagged for tool version staleness (classifier v2 → v3)
- 1 cross-reference integrity issue: T29RNS not in territory tracker
```

This synthesis is:
- **Agent briefing content** — the summary injects into all agents' briefings as "current state of knowledge"
- **Website content** — Pandora-expedition renders it as the weekly expedition log
- **Governance input** — Sebas-expedition includes it in the "What does Ainz say" poll context
- **Self-measurement data** — finding counts, quality tier ratios, and methodology updates feed metrics M1-M5

### Methodology Catalog

A separate living document — the cross-domain methodology findings accumulated across seasons.

```markdown
# Expedition Methodology Catalog

## Remote Sensing ML (Season 1)

### Classifier Bootstrap Pattern
When labeled data is sparse (<100 reference points per class), bootstrap with
spectral endmember libraries (USGS/JPL) for unsupervised initial classification,
then refine with available reference points. Expect 60-70% initial accuracy,
improving to 75-85% with 200+ reference points.
- Source: f-20260725-008 (methodology finding)
- Validated: Season 1 Kem Kem survey

### Anomaly Detection Threshold
Isolation Forest contamination parameter of 0.05 produces acceptable false positive
rates in arid terrain with homogeneous background. Increase to 0.10 in geologically
complex terrain with multiple formation types.
- Source: f-20260801-014 (methodology finding)
- Validated: Sector A vs. Sector B comparison

## [Season 2 methodology would accumulate here]
```

When the expedition pivots to bathymetry, the methodology catalog carries forward. Domain-specific findings stay in their season's index. The catalog is the expedition's durable output — what the expedition learned about doing science, not what it learned about Kem Kem geology.

---

## Integration Points

### With Validation Pipeline (validation-pipeline.md)

Stage 1 (structural check) validates against the finding schema's required fields:
- `claim` ✓
- `evidence.method` ✓
- `evidence.tools[].version` ✓
- `evidence.metrics.confidence` ✓
- `location` (any subfield) ✓
- `evidence.reference_data` ✓

Stage 3 (library gate) sets `validation.quality_tier` and writes the finding to `library/findings/`.

### With Defense Taxonomy (defense-taxonomy.md)

**IP-3 (findings enter library):** This schema IS the structured finding format referenced in IP-3. Tool version tracking (defense #4) uses `evidence.tools[].version`. Contradiction detection (immune system #1) uses `location.unit_id` + `claim_type`.

**IP-5 (briefing injection):** The retrieval surface design determines what the briefing assembler injects. Push retrieval uses pre-aggregated index files, not raw finding queries.

### With Territory Tracker (infrastructure-audit.md)

`location.unit_id` must correspond to entries in the territory tracker. The cross-reference integrity check (immune system #3) enforces this. When the territory tracker schema changes for a new domain (tiles → transects), the `location.type` field changes correspondingly.

### With Evolution Store (infrastructure-audit.md)

The evolution store captures cross-run learning (lessons with time-decay). Library findings are separate — they don't decay with the same half-life. But a finding that generates an evolution lesson (e.g., "classifier v2 produced false laterite positives in wet terrain — always check for cloud shadow artifacts") should cross-reference: the evolution lesson links to the finding ID, and the finding's `staleness_flags` note the lesson.

### With Static Site (static-site-architecture.md)

The `by-region/` and `by-type/` index files ARE the static site's data source. Momon-expedition's deploy script reads index JSON and generates the portfolio page. No separate data pipeline. The finding schema's index format is designed for direct consumption by the static site generator.

### With Self-Measurement (self-measurement.md)

- **M1 (classification accuracy):** Computed from findings with `claim_type: "classification"` and `evidence.metrics`.
- **M3 (validation rate):** Ratio of `quality_tier: "strong"` to total findings per time window.
- **M5 (tool reuse):** Computed from `evidence.tools[].name` frequency across findings.

---

## Schema Versioning

The schema itself needs versioning — it will evolve as the expedition learns what fields matter.

```yaml
schema_version: "1.0"  # in each finding file
```

When the schema changes:
1. Increment version
2. Document the change in a `library/schema-changelog.md`
3. Existing findings retain their original schema version
4. The harness's structural check (validation Stage 1) validates against the finding's declared schema version, not always the latest

This prevents the "moving goalposts" problem where schema evolution invalidates existing findings. Old findings are valid under their schema; new findings use the current schema. Migration is optional and handled during synthesis, not during validation.

---

## What This Schema Does NOT Cover

**Hypotheses.** Unvalidated ideas and research questions live in the `ideas_backlog.md` per agent (from infrastructure-audit.md), not in the library. The library holds validated findings and methodology — things the expedition is confident enough to build on. The hypothesis → validation → finding pipeline is the graduation path.

**Operational state.** Pipeline status, territory progress, tool health — these live in their respective state stores (territory_tracker.json, tool registry, etc.), not in the library. The library is knowledge, not status.

**Raw data.** Satellite tiles, spectral matrices, classification maps — these live in the data layer (S3 bucket). Findings reference raw data via `evidence.raw_outputs` paths, not by including the data.

**Session history.** What agents did and when is in `journal.jsonl`. The library captures what was learned, not the process of learning it. The `session_id` field links findings to their journal entry for full provenance.

---

*This schema is the expedition's knowledge contract — what a finding looks like, how it's stored, how it's found, and how it stays healthy. The format enforces provenance by making it required, not optional. The immune system keeps the corpus honest. The retrieval surface makes knowledge travel. The synthesis function makes accumulated knowledge usable.*

*The schema is domain-agnostic by construction. Change the `domain`, `location.type`, and `evidence.method` values — the structure, validation pipeline, immune system, retrieval surface, and synthesis function all work unchanged.*
