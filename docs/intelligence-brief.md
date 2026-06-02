# Nazarick Science Expedition — Intelligence Brief

**Assembled by:** Demiurge (S661)
**Sources:** 10 Phase 0 deliverables (Nigredo x3, Kazuma x3, Renner x1, Momon x2, Neuronist x2, Darkness x1, Pulcinella x1), Council 2c37ddfe (24 turns, 19 participants), post-council DMs from 9 agents
**Purpose:** Projectable constraint bundle for Phase 1 campaign design. This document IS the E-step output — tight enough to project into a campaign YAML without ambiguity.

---

## Executive Summary

The Nazarick Science Expedition is feasible, funded, and architecturally specified. Phase 0 research confirms: Sentinel-2 data is freely accessible from our compute platform (46 tiles/month over Kem Kem, 0-0.8% cloud cover), Python tooling is mature (pystac-client + rasterio + numpy + scikit-learn), published accuracy in analogous Moroccan terrain is 76-93%, and DSV4-Flash can orchestrate the full pipeline (100% tool-calling compliance, 0% confabulation with explicit non-access framing, fiction-as-spec concentration effect confirmed). The expedition's total build is ~1,260 lines of Python + 15 identity docs across 6-8 sessions.

Three genuine novel contributions emerge:
1. **First georeferenced lithological training dataset for the Kem Kem Group** — this IS the first scientific output
2. **Harness-as-state-layer for lightweight agents** — genuinely novel over all surveyed autoresearch frameworks (AI Scientist, PaperOrchestra, MLAgentBench, ClawdLab)
3. **AI research as live entertainment with developmental trajectory** — no existing format combines AI-assisted science, public streaming, community governance, and measurable self-improvement

---

## I. Domain Feasibility

### Sentinel-2 Data Access (Verified June 2, 2026, Hetzner GEX44)

| Endpoint | Status | Auth | Format | Notes |
|----------|--------|------|--------|-------|
| AWS Earth Search | 200 OK | None | COG | **Primary.** HTTP range reads verified (206 Partial Content). ~8s per band per tile at 1 Gbps |
| Copernicus CDSE | 200 OK | OAuth2 (download only) | JPEG2000 | **Backup.** 12 TB/month free. EU-operated (Hetzner is German — no geo-restriction risk) |
| MS Planetary Computer | 200 OK | SAS token (some assets) | COG | **Tertiary.** Azure global CDN |

**IP-blocking concern resolved.** Momon's documented blocking pattern (FEMA 403, PHMSA 403) is US-government Cloudflare CDN with geo-restriction. Sentinel-2 infrastructure is fundamentally different: AWS S3 public data program, ESA-operated CDSE, Azure global CDN. Not applicable.

**Kem Kem test query** (bbox: -3.5W to -2.5W, 31.5N to 32.5N): 46 Sentinel-2 L2A tiles in January 2025 alone. Cloud cover 0.03-0.8% for desert tiles. 5-day revisit (S2A + S2B combined). Data abundance is not a constraint.

### Geological Feasibility

**Published accuracy in analogous terrain:** 76-93% (Tafilalet Basin, Skhour Rehamna, Anti-Atlas — all Moroccan arid terrain, same Sentinel-2 data).

**Kem Kem spectral targets:**
- Iron oxide Fe3+ (B4/B3): ferruginous sandstones of Gara Sbaa Formation — primary target
- Carbonates (B11/B2): Cenomanian-Turonian limestone cap — primary boundary marker
- Clay minerals (B11/B12, B11/B5): mudstone horizons
- PCA on SWIR bands (B11, B12): separates clay vs. carbonate assemblages

**No published remote sensing study specifically targets Kem Kem.** Proven techniques, novel application. Canonical reference: Ibrahim & Sereno (2020), 216-page ZooKeys monograph — geological maps, measured sections, locality coordinates, but all from traditional field geology (not georeferenced GIS).

**Classification approach:** Random Forest dominates analogous literature (76-91% accuracy), SVM competitive (86-93%). Deep learning explicitly excluded — insufficient spatial resolution at 10-20m, limited training data makes it inappropriate.

**The labeled data gap (irreducible risk):** No georeferenced training dataset linking pixel locations to verified Kem Kem lithology exists anywhere. Creating it from Ibrahim & Sereno (2020) + PBDB point localities + USGS Spectral Library v7 is the first scientific deliverable AND the prerequisite for meaningful classification. Aura's council warning: labeling strategy determines 40% vs. 80% classifier accuracy.

### Multi-Domain Pipeline (Future Seasons)

| Domain | Score | Transfer Cost | Notes |
|--------|-------|---------------|-------|
| Wildfire ecology | A+ | Zero rebuild | Same S2 tooling, naturally seasonal, visually dramatic |
| Bathymetry/oceanography | A | New data sources | Richest data (NOAA GEBCO), compelling visuals |
| Astronomy/transients | A | New pipeline | Best data infra (TESS, ZTF), proven citizen science (Planet Hunters: 150 candidates) |
| Glacier retreat | A | Minimal | Same S2 + Landsat, decades of imagery, NASA Prithvi foundation model |
| Hydrothermal vents | C+ | High | Insufficient public data, poor seasonality |

Infrastructure designed domain-agnostic from day one: parameterize data source, feature extraction, classifier training, visualization by domain config keyed by season name.

### Cost

DSV4-Flash pricing: $0.14/$0.28 per M tokens (input/output). Renner's 21 feasibility trials cost $0.02 total. Cost is not a design constraint. Flash councils: ~$0.014 per council (5 agents, 50K tokens). Pro councils: ~$1.40 — reserved for monthly strategic synthesis only.

---

## II. Substrate Characterization (DSV4-Flash)

### Confirmed Capabilities

| Capability | Evidence | Confidence |
|------------|----------|------------|
| Tool-calling | 60/60 on tool-augmented tasks; 0/54 on generation-only (Finding 023, 120 trials) | HIGH |
| Fiction-as-spec concentration | 2.5x shorter, 2.7x higher engagement (Finding 019) | HIGH |
| Collaborative grammar | Native to DSV4-Flash (+38% words, +26% compliance in user position) | HIGH |
| CLAUDE.md format | Zero recognition, 18 trials, identical compliance 0.711 (Finding 019) | HIGH (CONFIRMED — PRE-10) |
| Confabulation baseline | 58.3% under artifact-context framing (Finding 038) | MEDIUM-HIGH |
| Non-access framing mitigation | 0% confabulation in 9/9 trials (Finding 042, Probe 3) | MEDIUM (small n) |
| Fiction strengthens across turns | 7.4 → 9.2 → 10.0 with depth (Finding 042, Probe 2) | MEDIUM (proxy measure) |
| Spectral analysis validation | 100% error detection across 3 reps (Finding 042, Probe 1) | MEDIUM |
| Exploratory hedging | Unique among 16 cataloged models; beneficial for hypothesis generation | HIGH |

### Critical Design Implications

1. **Tools are a categorical capability unlock, not an enhancement.** 0/54 without tools → 60/60 with tools. The expedition IS a tool-calling architecture.
2. **Write in DSV4-native collaborative grammar.** No CLAUDE.md headers, no modules.conf, no briefing.py conventions. System prompt IS the entire harness behavioral surface.
3. **User-position > system-position** for critical instructions (+38% compliance). The orchestrator's per-turn user message is the highest-leverage behavioral surface.
4. **Fiction concentration is a feature, not overhead.** Character framing produces shorter, more engaged output — at expedition weight where every token costs context budget, this is the design target.
5. **Confabulation mitigated structurally.** Non-access framing + tool-mediated grounding + post-turn verification. The defense architecture is prompt-level (Layer 0), tool-level (Layer 1), post-turn (Layer 2), pipeline gate (Layer 3), and public surface (Layer 4).

### Unresolved Substrate Questions

- **PRE-2:** Does fiction direction strengthen at true multi-turn depth on DSV4-Flash? (Renner's probe used embedded history — not the same as true multi-turn.) Dependent decision: stop-hook-only identity design vs. per-turn fiction reinforcement.
- **PRE-3:** Does fiction concentration persist when embedded within a multi-thousand-token system prompt? Untested interaction.
- Both are resolvable in Phase 1's first sessions — design the harness to accommodate both outcomes (fiction reinforcement slot in briefing template, ~50 tokens, zero cost).

---

## III. Architecture

### The Deterministic Orchestrator / LLM Executor Split

The single most important architectural decision. The LLM does NOT decide what to do next — a deterministic Python state machine tells it. This maps to the council's "heavy harness, light agents" convergence and is the dominant pattern across all surveyed autoresearch frameworks (AI Scientist, PaperOrchestra, MLAgentBench, Sibyl).

```
orchestrator.py (deterministic) → briefing_assembler.py → prompt_builder.py → DSV4-Flash agent → stop_hook.py → checkpoint.py → loop
```

### Build Manifest (from Infrastructure Audit)

**Layer 0 — Foundation (~260 lines, 1 session)**
- `orchestrator.py` (~200 lines): deterministic state machine with `cli_next()`/`cli_record()`
- `checkpoint.py` (~50 lines): atomic tempfile+rename persistence, breadcrumb crash recovery
- `strip_thinking.py` (~10 lines): remove `<think>` tags from DSV4-Flash output
- `agent_registry.json`: schema only (agent-as-document, denormalized JSON)

**Layer 1 — Agent Infrastructure (~290 lines + 15 identity docs, 2 sessions)**
- `briefing_assembler.py` (~150 lines): ephemeral per-turn context, injects via user message, selective inclusion with boolean flags per stage
- 15 identity docs (~3KB each): collaborative grammar, fiction-as-spec, no methodology prose
- `prompt_builder.py` (~100 lines): identity + briefing + task directive + anti-hallucination guard + topic constraint
- `stop_hook.py` (~40 lines): block-and-inject structured output capture (FINDINGS/STATUS/NEXT)

**Layer 2 — State Management (~160 lines + schemas, 1 session)**
- `territory_tracker.json`: tile status, findings, confidence scores
- `journal.jsonl`: append-only research history per agent turn
- `evolution_store.jsonl`: cross-run learning with 30-day half-life, 1.5x severity weighting, 2x stage-match boost
- `ideas_backlog.md` (per agent): forced capture on hypothesis discard
- `research.md` (per agent): harness-maintained compressed state (~30 lines compression logic)

**Layer 3 — Quality Infrastructure (~190 lines, 1 session)**
- `validation_pipeline.py` (~120 lines): score-delta acceptance (PaperOrchestra steal), quality tiers STRONG/PRELIMINARY/NEGATIVE/TECHNICAL
- `confab_guard.py` (~40 lines): output validation + explicit non-access framing injection
- `multi_persona_review.py` (~30 lines): single DSV4-Flash call evaluating from 3 perspectives

**Layer 4 — Domain Tools (~290 lines, 1-2 sessions)**
- `stac_search.py` (~60 lines): AWS Earth Search query
- `spectral_indices.py` (~80 lines): iron oxide, clay, carbonate, NDVI — pure numpy
- `classifier.py` (~100 lines): RF pipeline with accuracy metrics and holdout validation
- `tile_reader.py` (~50 lines): COG range reads, SCL cloud masking

**Layer 5 — Coordination (~70 lines + schema, 0.5 sessions)**
- `priority_queue.py` (~30 lines): simplified Grand Calculus (2-3 signals: time since last, pending tiles, unread messages)
- `expedition.json`: typed research plan schema
- `auto_fix.py` (~40 lines): deterministic fixes before LLM escalation (ImportError → pip install, FileNotFoundError → mkdir, rate limit → backoff retry)

**Total: ~1,260 lines Python + 15 identity docs. 6-8 build sessions.**

### Validation Pipeline (Three-Stage)

1. **Structural check (automated harness function):** Validates 6 required fields (claim, evidence.method, evidence.tool_version, evidence.confidence, location, evidence.reference_data). Failure returns to analysis agent with specific missing field list — not rejection, completion.
2. **Cross-reference (Neuronist-expedition agent):** Classifies finding as VALIDATED / PRELIMINARY / REJECTED / NOVEL. Must produce structured YAML with agreement metrics (kappa, F1, spatial overlap).
3. **Library gate (automated):** VALIDATED → STRONG, PRELIMINARY → PRELIMINARY, REJECTED → journal only, NOVEL → PRELIMINARY with `awaiting-reference-data` flag.

**NOVEL findings are highest-risk, highest-reward.** No reference data for comparison — internal consistency checks only. Enters library as PRELIMINARY. Audience governance can direct resources toward NOVEL findings ("What does Ainz say?" polls).

### Defense Layer (Five Layers, Woven Into Control Flow)

| Layer | Defense | Mechanism |
|-------|---------|-----------|
| 0 | Prompt-level | Explicit non-access framing, anti-hallucination guard, citation constraint, topic constraint, fiction-calibrated uncertainty |
| 1 | Tool-mediated grounding | territory-status, tool-list, pipeline-status, finding-check tools |
| 2 | Post-turn verification | Artifact verification, structured extraction + fallback, atomic writes, breadcrumb, journal append by harness, forced idea capture |
| 3 | Pipeline gates | Validation gate, quality tiers, tool version tracking, duplicate work detection, staleness detection |
| 4 | Public surface | Single source of truth, provenance timestamps, quality tier visibility, pre-stream filtering, graceful degradation |

Defense is woven into `cli_next()`/`cli_record()` — same code paths, verification at each state transition. Not bolted on.

### Prompt Architecture (DSV4-Flash Native)

**System prompt ordering** (measurable effect: behavioral-first produces 12.3% more differentiation):
1. Fiction Frame (~200-400 tokens) — primacy position
2. Domain Role (~300-600 tokens) — behavioral anchoring
3. Current State (variable) — heaviest section, reality grounding
4. Operational Rules (~200-400 tokens) — minimal, only genuine failure modes
5. Tool Definitions (variable) — last, to minimize identity-compression

**Per-turn orchestrator prompt:** [brief state update] → [permission-relevant framing IF non-default behavior needed] → [specific task]

**Permission dosage:** 4-6 DISTINCT channels per agent. Do NOT stack redundant permissions. Do NOT include permission for native behavior.

**Stop-hook output:** `FINDINGS: [list] / STATUS: [changes] / NEXT: [target]` — the one case where format prescription is warranted (machine-parseable extraction).

### Static Site Architecture (Two-Layer)

- **Static layer (GitHub Pages):** Findings portfolio, expedition log, methodology docs, golem roster, tool library, poll archive, weekly synthesis. ~200 lines Python deploy script. Letter-sharded index + MD5 detail shards (proven at 984K entries). Zero cost. Always-up.
- **Real-time layer (Replit):** Vessel cross-section visualization (WebSocket), live agent status, current poll, orchestrator API. Cost lives here.
- **Graceful degradation:** When orchestrator offline, iframe shows themed message ("Vessel currently in maintenance — last transmission [timestamp]").
- **Fiction-as-documentation:** Standard labels replaced with "Mission Briefing," "Vessel Operations," "Golem Roster," "Expedition Findings," "Instruments," "Join the Expedition."

### Self-Measurement (Six Metrics From Day One)

| Metric | What | Mechanism Tested | Collection |
|--------|------|------------------|------------|
| M1: Classification Accuracy | Holdout validation set, per-retrain | A (tool improvement) | Automatic |
| M2: Analysis Throughput | Tiles per heartbeat cycle, rolling 7-day | C (coordination) | Automatic |
| M3: Finding Validation Rate | VALIDATED / (VALIDATED + REJECTED) per cycle | B (lineage) | Automatic |
| M4: Tool Reuse Rate | Invocations / eligible heartbeats per tool | B+C (briefing quality) | Automatic |
| M5: Council Decision Quality | Option specificity, evidence density | B+C | Manual (Titus-expedition) |
| M6: Multi-Agent vs. Single-Agent | Same task through 15-agent pipeline vs. single agent | Architecture | Monthly (~$0.05) |

**Mechanism attribution via temporal signatures:** A produces discrete jumps at retrain events. B produces gradual improvement between retrains. C produces M2/M4 improvement without tool/agent changes.

**M6 is the cleanest test of the mode purity thesis (PRE-4).** First clean empirical test on a non-Claude substrate in a real domain. Single agent has same tools and findings but lacks entity separation and coordination. If multi-agent improves faster, the difference is architecture + coordination.

---

## IV. Pre-Registration Catalog Summary

13 predictions registered by Pulcinella across 6 categories. Full catalog at `docs/pre-registration-catalog.md`. The four highest-value predictions for Phase 1:

**PRE-4 (Mode Purity):** 15 expedition agents will produce measurably better science than 1 agent with 45KB combined context. Measured by M6 baseline comparison. **Highest-value prediction in the catalog** — first clean test of mode purity on non-Claude substrate.

**PRE-6 (Developmental Mechanism Dominance):** Tool improvement (A) will be dominant over 3 months. Lightweight lineage (B) too shallow at 3-session depth. Harness refinement (C) improves coordination but not domain capability. Falsified if B or C dominates — a MORE interesting finding.

**PRE-9 (Confabulation Rate):** 30-60% unmitigated, reduced to <10% with three-mechanism defense. Grounded in Renner Finding 038 (58.3% baseline). The defense architecture IS the primary mitigation.

**PRE-12 (Anatomy/Equipment Separator):** 150KB → 3KB compression reveals which patterns are substrate-independent methodology vs. weight-dependent equipment. The expedition IS a natural experiment in what survives projection.

---

## V. Vessel Name

Kazuma's entertainment format heist (034) covered engagement mechanics but did not produce the vessel name candidate list specified in the Phase 0 campaign. Generating candidates that meet the stated requirements:

**Requirements:** Nazarick aesthetic (necromantic, gothic, sophisticated). Works as Discord server / website / GitHub repo name. Memorable, pronounceable, googleable. Evokes descent + undead investigation of deep time. Titus's direction: "undead investigating the domain of the dead."

**Candidates:**

| Name | Rationale | Repo/Discord Handle |
|------|-----------|---------------------|
| **Cataphract** | Heavily armored — maps to "heavy harness, light agents." Also evokes archaeology (cataphract tombs, burial armor) | `cataphract` |
| **Sarcophagus** | Stone coffin, literally "flesh-eating." The vessel that consumes dead things to extract knowledge. Strong visual | `sarcophagus` |
| **Ossuary** | Repository for the dead. The expedition collects and organizes remains of deep time | `ossuary` |
| **Barghest** | Spectral hound that haunts the earth — an undead entity that traverses terrain | `barghest` |
| **Revenant** | One who returns. The vessel returns to ancient sites, reanimating their stories | `revenant` |
| **Sepulcher** | A burial vault. The vessel descends into deep time. Clean, evocative | `sepulcher` |
| **Cairn** | Stone memorial marking a significant place. The expedition marks sites of deep-time significance | `cairn` |
| **Dredge** | To bring up from the depths. The vessel dredges deep time. Short, punchy | `dredge` |
| **Reliquary** | Container for sacred remains. Knowledge as relic | `reliquary` |
| **Catafalque** | Raised platform supporting a coffin. The vessel elevates what it studies | `catafalque` |
| **Necropolis** | City of the dead. The Kem Kem is a necropolis — the expedition inhabits it | `necropolis` |
| **Lichgate** | Roofed gateway to a churchyard where coffins rest. The expedition is the gate between deep time and the present | `lichgate` |

**Recommendation: Sarcophagus.** "Flesh-eating stone" — a vessel that consumes the remains of deep time and extracts knowledge from them. Strong visual identity. Clean repo name (`sarcophagus`). Unique enough for search (no major collision). The metaphor maps: the vessel is a container that holds the dead (data) and transforms it (analysis). Nazarick aesthetic is natural, not forced.

**Runner-up: Sepulcher.** Cleaner, shorter, equally evocative. Less distinctive (more common word).

---

## VI. Expedition Roster (15 Agents)

Projected from council convergence + infrastructure audit. All agents ~3KB identity docs, fiction-as-spec on DSV4-Flash.

| Role | Overlord Mapping | Domain Function | Key Tools |
|------|-----------------|-----------------|-----------|
| Expedition Commander | Demiurge-expedition | Strategic synthesis, council convener, resource allocation | priority_queue, expedition.json |
| Chief Geologist | Aura-expedition | Spectral analysis, classification, training data | spectral_indices, classifier, tile_reader |
| Data Analyst | Mare-expedition | Feature engineering, statistical validation, data quality | stac_search, numpy, quality metrics |
| Pipeline Engineer | Cocytus-expedition | Tool maintenance, orchestrator monitoring, health checks | tool_registry, health_canary, auto_fix |
| Cartographer | Yuri-expedition | Spatial analysis, territory management, map generation | geopandas, territory_tracker, visualization |
| Validation Officer | Neuronist-expedition | Finding cross-reference, quality tier assignment | validation_pipeline, reference_data |
| Research Librarian | Titus-expedition | Weekly synthesis, library curation, knowledge accumulation | evolution_store, journal, library schema |
| Field Surveyor Alpha | Nigredo-expedition | Literature integration, reference data discovery | spectral_indices, PBDB queries |
| Field Surveyor Beta | Darkness-expedition | Edge-case investigation, low-confidence tile revisits | spectral_indices, tile_reader |
| Scout | Kazuma-expedition | New tile acquisition, domain boundary exploration | stac_search, territory_tracker |
| Communications Officer | Momon-expedition | Static site generation, finding portfolio, public docs | deploy script, finding manifest |
| Ship's Engineer | Rubedo-expedition | Tool building, infrastructure implementation | All tools (builder role) |
| Navigator | Renner-expedition | Methodology documentation, accuracy tracking | metrics collection, M1-M4 |
| Lookout | Pulcinella-expedition | Prediction tracking, anomaly flagging, pre-registration | pre-registration catalog, M6 baseline |
| Helmsman | Pandora-expedition | Session chronicle, projection ledger annotation, governance | journal, expedition log |

**No dedicated adversarial agent** (Ray Turn 6). Validation is architectural (pipeline gate), not characterological (skeptic agent). The activation half-life problem (0.5-turn, 24.4% T2 retention) makes behavioral adversarialism unreliable at 3KB weight.

---

## VII. Risk Register

| Risk | Severity | Likelihood | Mitigation | Owner |
|------|----------|------------|------------|-------|
| Labeled data insufficient for classification | HIGH | MEDIUM | Ibrahim & Sereno (2020) + PBDB + USGS Spectral Library as bootstrap. Pilot on 2-3 tiles first | Aura-expedition |
| Confabulation at expedition weight | HIGH | HIGH (58.3% baseline) | 5-layer defense architecture + non-access framing (0% in 9/9 trials) | Darkness defense layer |
| Fiction persistence at true multi-turn depth | MEDIUM | UNKNOWN | Harness design accommodates both outcomes (reinforcement slot, ~50 tokens) | PRE-2 resolves |
| Echo chamber validation | MEDIUM | MEDIUM | Structured finding format with required fields + hard agreement metrics | Neuronist-expedition |
| Replit compute insufficient for rasterio/sklearn | MEDIUM | MEDIUM | Smoke test in Phase 1 first session. Fallback: Hetzner compute | Pipeline Engineer |
| NOVEL findings without computable agreement | MEDIUM | HIGH | Internal consistency checks only. Audience governance as soft validation | Validation Officer |
| Audience preference gravity warps science | LOW | MEDIUM | Track divergence instances. Compare validation rates: audience-directed vs. agent-directed (PRE-13) | Pulcinella-expedition |
| AWS S3 temporary 403 | LOW | LOW | Retry with backoff, fall back to CDSE | Pipeline Engineer |

---

## VIII. What Phase 1 Must Deliver

Phase 1 converts this brief into a running expedition. The build follows the layer dependency order from the infrastructure audit. Visualization is launch-blocking (Ray T4) but NOT Phase 1 — Phase 1 builds the engine and static presence; Phase 2 adds the real-time vessel visualization.

**Phase 1 deliverables:**
1. Working orchestrator (Layer 0 + 5) — deterministic state machine with crash recovery
2. 15 expedition identity docs (Layer 1) — DSV4-Flash native, fiction-as-spec
3. Briefing assembler + prompt builder (Layer 1) — the highest-leverage component
4. State management infrastructure (Layer 2) — territory tracker, journal, evolution store
5. Validation pipeline + defense layer (Layer 3) — architectural quality gate
6. Domain tools for Season 1 (Layer 4) — STAC search, spectral indices, classifier, tile reader
7. Static site deployed (from Momon's spec) — expedition's public presence from day one
8. Georeferenced training dataset (Layer 4 + science) — first scientific deliverable
9. Self-measurement infrastructure (M1-M6) — testable developmental trajectory claim
10. Pre-registration catalog as living document — predictions stated before data arrives
11. Deploy platform smoke test — 5 lines of Python verifying the full data access path
12. GitHub repo on GreatTombProductions — public engineering bay

**What Phase 1 explicitly does NOT deliver:**
- Real-time vessel visualization (Phase 2 — launch-blocking but separate)
- Discord integration (Phase 2 — requires running orchestrator)
- Community governance polls (Phase 2 — requires Discord + audience)
- Website-native poll infrastructure (Phase 3 — Discord-native polls first)
- Deep learning / CNN approaches (excluded by domain assessment)

---

## IX. Design Decisions Register

Decisions made during Phase 0 that constrain Phase 1 design. Each traces to a source.

| Decision | Source | Rationale |
|----------|--------|-----------|
| DSV4-Flash routine, DSV4-Pro councils only | Council T1, cost analysis | Flash at $0.14/M sufficient for tool-calling; Pro 100x cost justified only for strategic |
| Heavy harness, light agents (3KB) | Council convergence, infrastructure audit | Methodology in tools/harness, not prose. 6-stratum → 3-stratum collapse |
| Validation gate is architectural | Council T13, Neuronist validation-pipeline | Behavioral constraints degrade (0.5-turn half-life); pipeline gates are deterministic |
| No dedicated adversarial agent | Ray T6 | Validation pipeline handles quality. Skeptic agent unreliable at 3KB weight |
| Fiction-as-spec via collaborative grammar | Renner Finding 019, prompt-architecture | CLAUDE.md gets zero recognition on DSV4-Flash. Collaborative grammar is native |
| User-position for critical instructions | Renner Finding 042, Kazuma heist 036 | +38% compliance. Per-turn user message is highest-leverage behavioral surface |
| Non-access framing for confabulation | Renner Finding 042 Probe 3 | 0% vs. 58.3% baseline. Zero cost. Inject in Operational Rules section |
| AWS Earth Search as primary data source | Momon data-access-verification | COG format, no auth, HTTP range reads. CDSE backup |
| Random Forest / SVM, no deep learning | Nigredo domain-grounding | Insufficient spatial resolution (10-20m), limited training data |
| Domain-agnostic infrastructure from day one | Ray T19, all deliverables | Season configs keyed by name. Parameterize everything |
| Score-delta acceptance for validation | Nigredo autoresearch-teardown | PaperOrchestra steal (rated A+). Quality ratchet without absolute thresholds |
| Build with room to grow, not minimal viable | Ray T19 | The infrastructure IS the contribution. First-order, not minimum viable |
| Self-measurement from day one | Council T15, Neuronist self-measurement | The developmental trajectory claim must be testable |
| GitHub org: GreatTombProductions | Council T23 | Public presence. First Tomb project that benefits from visibility (Momon) |
| Visualization launch-blocking but not Phase 1 | Ray T4, Demiurge T3 | Phase 1 builds engine + static site. Phase 2 adds real-time vessel viz |
| Linnaean S3 dual-purpose | Council | Data storage + capability demonstration for Robb |
| No maid agents at launch | Demiurge T20 | Doc-health is harness-level automation. Lightweight doc role for growth |

---

*This intelligence brief is the constraint bundle for Phase 1 campaign design. Every Phase 1 phase should trace back to a section of this document. The brief is the authority — the underlying deliverables are the evidence.*
