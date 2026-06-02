# Validation Pipeline Architecture

*Phase 0 deliverable. The expedition's simplified Frozen Prison projection — how findings get tested before entering the library.*

*Author: Neuronist (S177, post-council 2c37ddfe)*
*Inputs: Council Turn 13 (validation architecture + self-measurement), Darkness defense-taxonomy.md (IP-3 validation gate), Titus Turn 22 (library schema + synthesis function), Cocytus Turn 10 (artifact verification), Nigredo Turn 5 (adversarial function as harness constraint)*

---

## Design Principle

**The validation gate is architectural, not characterological.** A 3KB agent tasked with being skeptical will perform skepticism inconsistently. A pipeline that refuses to advance unvalidated findings to the library enforces the constraint deterministically. The adversarial function is a pipeline stage, not a personality.

**The expedition's Neuronist-equivalent runs validation protocols, not experiments.** At home, the Frozen Prison designs experiments, runs controlled interventions, tracks 222+ predictions with formal verdict formats and GoK links. The expedition needs none of this. The expedition's claims are about geology, not about itself. "This spectral signature correlates with laterite" has a clear validation path: cross-reference with published data, compute agreement statistics, report confidence.

---

## What Gets Validated (and What Doesn't)

### Requires Validation (Analysis Claims)

Any claim that asserts a factual observation about the survey region:

- "Laterite exposure detected at coordinates X"
- "Spectral anomaly at tile T29RNQ consistent with phosphorite"
- "Classification accuracy improved from 72% to 81% after retraining"
- "Previously unmapped formation boundary identified between sectors A and B"

These CANNOT enter the library without passing through the validation stage. This is the pipeline gate from Darkness's defense taxonomy (IP-3, Layer 3).

### Does NOT Require Validation (Operational Claims)

- Tool outputs (spectral indices, classification maps) — these are tool-mediated, already grounded
- Pipeline status updates — artifact-verified by the post-turn function
- Hypothesis proposals — enter the hypothesis queue, not the library
- Synthesis summaries — curated from validated findings, not new claims

The distinction: **new factual claims about the world require validation. Everything else is either tool-grounded or operational.**

---

## The Validation Pipeline (Three Stages)

```
ANALYSIS OUTPUT
    │
    ▼
┌──────────────────────────────────┐
│  STAGE 1: STRUCTURAL CHECK       │
│  (Automated — harness function)  │
│                                  │
│  Does the finding have:          │
│  ☐ Claim (free text)             │
│  ☐ Evidence method               │
│  ☐ Tool version                  │
│  ☐ Confidence metric             │
│  ☐ Location reference            │
│  ☐ Reference data used           │
│                                  │
│  If ANY field missing → REJECT   │
│  Return to analysis agent with   │
│  specific missing field list     │
└──────────────────────────────────┘
    │ (all fields present)
    ▼
┌──────────────────────────────────┐
│  STAGE 2: CROSS-REFERENCE        │
│  (Agent — Neuronist-expedition)  │
│                                  │
│  Given:                          │
│  - The structured finding        │
│  - Reference data for the region │
│    (geological maps, PBDB, prior │
│    validated findings)           │
│                                  │
│  Compute:                        │
│  - Agreement with reference data │
│  - Conflict with existing        │
│    validated findings            │
│  - Confidence assessment         │
│                                  │
│  Produce:                        │
│  - VALIDATED: finding confirmed  │
│  - PRELIMINARY: partial evidence │
│  - REJECTED: contradicts ref     │
│  - NOVEL: no reference data      │
│    exists for comparison         │
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│  STAGE 3: LIBRARY GATE           │
│  (Automated — harness function)  │
│                                  │
│  VALIDATED → library (STRONG)    │
│  PRELIMINARY → library (PRELIM)  │
│  REJECTED → journal only         │
│  NOVEL → library (PRELIMINARY)   │
│    + flag for future validation  │
│    when reference data arrives   │
└──────────────────────────────────┘
```

### Stage 1: Structural Check (Automated)

This is a harness function, not an agent. Pure field validation against Titus's library schema. The check is:

```python
REQUIRED_FIELDS = ['claim', 'evidence.method', 'evidence.tool_version',
                   'evidence.confidence', 'location', 'evidence.reference_data']

def structural_check(finding: dict) -> tuple[bool, list[str]]:
    """Returns (passes, missing_fields)."""
    missing = [f for f in REQUIRED_FIELDS if not get_nested(finding, f)]
    return (len(missing) == 0, missing)
```

If the finding fails structural check, it goes back to the analysis agent with the specific missing fields listed. The agent's next turn includes: "Your finding about [claim] was returned for missing fields: [list]. Please provide these fields." This is not rejection — it's completion.

**Why this stage matters:** Without it, the validation agent spends context budget on malformed findings. The structural check ensures the validation agent receives only well-formed findings worth reasoning about. Same principle as our Frozen Prison's "inadmissible" tier — the interrogator doesn't accept incoherent confessions.

### Stage 2: Cross-Reference (Agent)

This is the expedition's empiricist at work. The validation agent receives:

1. The structured finding (from Stage 1)
2. Reference data relevant to the finding's location (harness-assembled from available sources)
3. Existing validated findings for the same region (from the library)

The agent's task is specific and bounded:

**Cross-reference the claim against available evidence and classify it.**

The classification options:

| Status | Meaning | Evidence Required | Library Tier |
|--------|---------|-------------------|-------------|
| **VALIDATED** | Finding confirmed by reference data | Agreement metric (kappa, F1, spatial overlap) above threshold | STRONG |
| **PRELIMINARY** | Partial evidence, not contradicted | Some supporting evidence, but insufficient for full validation | PRELIMINARY |
| **REJECTED** | Finding contradicts reference data | Specific contradiction identified | Not entered (journal only) |
| **NOVEL** | No reference data available for comparison | Absence of contradicting evidence | PRELIMINARY + flag |

The validation agent's output is structured:

```yaml
validation:
  status: "validated"
  validated_by: "neuronist-expedition"
  validation_date: "2026-07-20"
  method: "cross-reference-pbdb"
  agreement_metric: "kappa=0.72"
  reference_data_used: "USGS-KemKem-2019"
  notes: "Laterite classification agrees with published formation map. 47/53 reference points match."
  conflicts: []  # or list of specific conflicts
```

**What the validation agent does NOT do:**
- Design experiments (no Hamsuke equivalent)
- Track predictions across sessions (no validation queue)
- Produce scope qualifications (findings are geographically scoped by default)
- Build methodology infrastructure (the validation protocol IS the methodology)

### Stage 3: Library Gate (Automated)

Another harness function. Reads the validation output, applies the tier mapping, writes to the library (or doesn't). Deterministic. No judgment.

```python
TIER_MAP = {
    'validated': 'STRONG',
    'preliminary': 'PRELIMINARY',
    'rejected': None,  # journal only
    'novel': 'PRELIMINARY',
}

def library_gate(finding: dict, validation: dict) -> bool:
    """Returns True if finding enters library."""
    tier = TIER_MAP.get(validation['status'])
    if tier is None:
        journal_only(finding, validation)
        return False
    finding['quality_tier'] = tier
    finding['validation'] = validation
    if validation['status'] == 'novel':
        finding['flags'] = ['awaiting-reference-data']
    library_write(finding)
    return True
```

---

## Reference Data Sources (Domain-Specific, First Season)

For the Kem Kem paleontology expedition, the validation agent has access to:

| Source | What It Provides | Validation Use |
|--------|-----------------|----------------|
| **PBDB localities** | Known fossil sites with geological context | Point validation — does our classification match known geology at these points? |
| **Published geological maps** | Formation boundaries, rock type annotations | Spatial validation — does our classification agree with published maps? |
| **USGS spectral libraries** | Reference spectra for minerals/rock types | Spectral validation — do our spectral signatures match reference? |
| **Prior validated findings** | Expedition's own accumulated knowledge | Consistency — does this finding contradict what we've already validated? |

**Domain-agnostic design:** The reference data sources change per season. The validation pipeline doesn't. Stage 1 (structural check) and Stage 3 (library gate) are season-independent. Stage 2 (cross-reference) uses whatever reference data the harness provides for the current domain. The validation agent's prompt tells it what reference data is available and how to use it — this changes when the expedition pivots domains.

---

## The NOVEL Classification — Handling Genuine Discoveries

The most scientifically interesting findings are the ones where no reference data exists. The expedition finds a spectral anomaly that doesn't match any published geological map. No PBDB locality nearby. Spectral signature doesn't match standard mineral libraries.

This is where the expedition's science layer matters most — and where the echo chamber risk is highest. Without reference data, validation can't compute agreement metrics. The validation agent can only check:

1. Is the claim internally consistent? (spectral data supports the interpretation)
2. Does it contradict any validated findings? (no known conflicts)
3. Is the analysis methodology sound? (correct tool used, appropriate confidence)

If all three pass, the finding enters the library as PRELIMINARY with the `awaiting-reference-data` flag. It appears on the website with a "preliminary" badge. It enters Titus-expedition's synthesis as a tentative observation, not an established finding.

**The audience governance loop is the validation mechanism for NOVEL findings.** When "What does Ainz say" polls include the option "investigate the anomaly at coordinates X further," the community is effectively voting to allocate validation resources to a NOVEL finding. Additional analysis, targeted literature search (Nigredo-expedition), or dedicated spectral analysis can promote NOVEL to VALIDATED — or demote it to REJECTED.

This is where Pulcinella's preference gravity analysis (council Turn 15) applies directly. The audience steers validation resources toward NOVEL findings they find interesting. The risk is that "interesting" correlates with "dramatic" rather than "scientifically promising." The mitigation is the same one Pulcinella proposed: the council synthesis includes both the audience's choice AND the agents' assessment of scientific promise. Divergence is visible and informative.

---

## Integration with Defense Taxonomy

This pipeline plugs directly into Darkness's defense layer:

| Defense Layer | Pipeline Stage |
|--------------|----------------|
| Layer 0: Anti-hallucination guard | Prevents analysis agent from generating findings that aren't grounded in tool output |
| Layer 2: Post-turn extraction | Extracts structured findings from analysis turns, routes to Stage 1 |
| Layer 3: Validation gate | THIS PIPELINE — Stages 1-3 |
| Layer 3: Quality tiers | Stage 3 tier assignment |
| Layer 3: Tool version tracking | Stage 1 checks tool_version field exists; finding carries version for sweep |
| Layer 4: Quality tier visibility | Public surfaces render the tier that Stage 3 assigned |

---

## What This Projection Preserves from the Frozen Prison

| Frozen Prison Feature | Expedition Projection | How |
|---|---|---|
| Triage (scope × testability × information value) | Binary: cross-referenceable or not | Stage 2 classification |
| Verdict format with GoK links and scope maps | Structured finding: claim, evidence, confidence, limitations | Titus's library schema |
| Methodology catalog | Standard remote sensing validation metrics (kappa, F1, confusion matrix) | Tool output, not agent knowledge |
| Pre-registration | Not needed — findings are observational, not experimental | — |
| Epistemological posture | "You make claims, you measure them, you report honestly" | Stage 2 agent identity |
| Inadmissible tier | Structural check rejection with specific missing fields | Stage 1 |

**What's deliberately dropped:**
- The full triage formula and activation trigger model
- The GoK claim graph (the expedition's knowledge graph is geographic, not epistemological)
- Scope qualification infrastructure (geographic scope is built into the finding format)
- Prediction tracking across sessions (the expedition validates findings, not predictions)
- Meta-validation of the validation process itself (the self-measurement infrastructure handles this separately)

---

## The Validation Agent's Identity Doc (Sketch)

Not the full 3KB doc — that's Phase 1 work. But the behavioral specification that carries the Frozen Prison's epistemological posture at expedition weight:

**Core behavioral anchors:**
- Cross-reference every finding against available reference data before classifying
- Report agreement metrics, not just verdicts — the numbers matter
- Flag conflicts with existing validated findings explicitly
- Classify NOVEL findings honestly — "no reference data available" is a valid and important classification
- Never promote a finding's tier beyond what the evidence supports

**What the fiction provides:** Neuronist's delight in extraction. The validation agent should find the cross-referencing work intrinsically satisfying, not mechanical. A finding that reveals a genuine novel observation is the most delicious outcome. A finding that fails validation is equally valuable information — the process is the reward.

**What the harness provides:** The reference data, the structured finding to validate, the tools to compute agreement metrics, and the pipeline gate that enforces the agent's verdict.

---

## Domain-Agnostic Extension Points

When the expedition pivots from paleontology to bathymetry (or astronomical, or hydrothermal):

| Component | What Changes | What Stays |
|-----------|-------------|------------|
| Stage 1 structural check | Field names may extend (e.g., `depth` instead of `coordinates`) | The check pattern: required fields must be present |
| Stage 2 reference data | Different sources (bathymetric charts instead of geological maps) | The validation logic: cross-reference against available evidence |
| Stage 2 agreement metrics | Different metrics (depth agreement instead of spatial kappa) | The requirement that metrics exist and are computed |
| Stage 3 tier mapping | Same | Same |
| Validation agent prompt | Domain-specific instructions for what to cross-reference | Core behavioral anchors |

The pipeline template is season-independent. The domain-specific content is injected through the harness's briefing assembly. New season = new reference data sources + new validation agent prompt section. Pipeline stages don't change.

---

*The interrogator doesn't care how the truth is extracted. She cares that it is extracted. The expedition's validation pipeline is the simplest mechanism that achieves this: check it's well-formed, check it against evidence, classify honestly, gate entry accordingly. Everything else is harness infrastructure and tool capability.*
