# Nazarick Science Expedition

The Sorcerer Kingdom's second high-resolution projection. A continuously developing autoresearch ecosystem that investigates Earth's deep history through remote sensing, ML tool development, and paleontological data analysis — performed by Overlord-mapped agents remotely piloting a research vessel, in public, at human reading speed, with community governance.

---

## Status

**Phase 0: Intelligence Brief** — COMPLETE. All 8 campaign phases delivered. Intelligence brief assembled at `docs/intelligence-brief.md`. Phase 1 campaign drafted.

**Phase 1: Expedition Build** — Campaign `nse-phase-1-expedition-build` active. 13 phases, 3 workstreams.
- **Layer 0+5 (Orchestrator Foundation + Coordination):** COMPLETE. Full pipeline verified: orchestrator → invoke → Gemini 2.5 Flash → parse → record. Harness: orchestrator.py (deterministic state machine), checkpoint.py (atomic writes + breadcrumb), strip_thinking.py, priority_queue.py (signal-weighted scheduling), auto_fix.py (deterministic error recovery), invoke.py (Gemini API bridge via google-genai SDK), output_parser.py (FINDINGS/STATUS/NEXT extraction), run_expedition.py (main entry point with bounded iteration, graceful shutdown, structured logging). State schemas: agent_registry.json (15 agents), expedition.json (season config + stage contracts), territory_tracker.json. Live test: scout agent found 14 Sentinel-2 tiles, structured output parsed successfully.
- **Layer 1b (Briefing Assembler + Prompt Builder):** COMPLETE. briefing_assembler.py (context-flag-driven state injection from live stores), prompt_builder.py (5-section DSV4-Flash native system prompt: fiction frame → domain role → current state → operational rules → tool definitions). Replaces Layer 0 stub prompts in invoke.py. User messages in collaborative grammar (+38% compliance). Fiction refresh, anti-hallucination guard, topic constraint all wired.
- **Layer 2 (State Management Infrastructure):** COMPLETE. territory_manager.py (tile lifecycle: add/update/query/findings/classification, status transition validation), journal_manager.py (query/filter/aggregate over journal.jsonl), evolution_store.py (cross-run learning: 30-day half-life, 1.5x severity weighting, 2x stage-match boost), state_manager.py (unified facade + ideas backlog + research state compression). Post-invoke hook wired: turn results auto-flow into research state and evolution store. Live test: full pipeline with state management verified on Gemini 2.5 Flash.
- **Layer 3 (Validation Pipeline + Defense Layer):** COMPLETE. validation_pipeline.py (three-stage: structural → cross-reference → library gate), confab_guard.py (pattern detection + non-access framing), multi_persona_review.py (3-persona DSV4-Flash review). Quality tiers: STRONG/PRELIMINARY/NEGATIVE/TECHNICAL. Wired as orchestrator post-invoke hooks.
- **Layer 4 (Domain Tools for Season 1):** COMPLETE. tile_reader.py (COG range reads, SCL masking), stac_search.py (AWS Earth Search STAC), spectral_indices.py (iron oxide, carbonate, clay, NDVI, SWIR PCA — pure numpy), classifier.py (RF pipeline, holdout validation, tile prediction).
- **Self-Measurement Infrastructure (M1-M6):** COMPLETE. metrics_collector.py — six metrics tracking developmental trajectory: M1 (classification accuracy, post-retrain hook), M2 (throughput, periodic aggregation from territory tracker), M3 (validation rate, periodic aggregation from findings log), M4 (tool reuse, periodic aggregation from journal), M5 (council quality, manual recording by Titus-expedition), M6 (baseline comparison, monthly measurement heartbeat). Wired into orchestrator (metrics_collect hook), run_expedition.py (periodic aggregation on run completion, --metrics flag), classifier.py (M1 auto-recording on retrain), briefing_assembler.py (metrics summary injected for synthesize/maintain/validate stages). CLI: `python3 harness/metrics_collector.py report|summary|aggregate|trend`. Storage: `metrics/*.jsonl`. Live: first aggregation populated M3 + M4 from existing state data.

---

## Origin

- **Council 2c37ddfe** (2026-06-01): 19 participants, 24 turns. Vision document from strategic instance, specialist input from all domain experts.
- **Projection Ledger:** Second entry after gemba3. Entry in `sorcerer-kingdom/projection-ledger/entries/nazarick-science-expedition.md`.

## Architecture (from council convergence + Phase 0 research)

- **Heavy harness, light agents.** ~3KB identity docs on DSV4-Flash. The harness carries coordination intelligence; agents carry differentiation; beasts carry computation.
- **Fiction-as-specification** confirmed on DSV4-Flash (Renner Finding 019). Concentration effect (2.5x shorter, 2.7x higher engagement).
- **Validation gate is architectural, not characterological.** Pipeline stage enforces: analysis → validation → library entry. No dedicated adversarial agent.
- **Three developmental mechanisms:** Tool improvement (A), lightweight lineage (B), harness refinement (C). All three enabled.
- **Self-measurement infrastructure from day one.** Six metrics (M1-M6) tracking developmental trajectory.
- **Domain-agnostic design.** First season: North African paleontology via Sentinel-2. Future seasons: wildfire ecology (A+), bathymetry (A), astronomy (A), glacier retreat (A).
- **Deterministic orchestrator / LLM executor split.** The harness decides what to do; agents execute. ~1,260 lines Python + 15 identity docs.
- **Five-layer defense.** Prompt-level (non-access framing: 0% confab in 9/9 trials) → tool-mediated grounding → post-turn verification → pipeline gates → public surface filtering.
- **DSV4-Flash native.** Collaborative grammar, user-position injection (+38% compliance), no CLAUDE.md conventions (zero recognition on DSV4-Flash).

## Five-Dimension Blueprint

| Dimension | Specification |
|-----------|---------------|
| **Model** | DSV4-Flash (routine) + DSV4-Pro (councils). Single-substrate by design |
| **Harness** | Projected orchestrator. Keeps: heartbeat scheduling, agent state, tool-calling, audit. Strips: convergence strategies, substrate routing, worktree isolation. Adds: Discord streaming, token throttling, community governance |
| **Context** | Lightweight identity docs (~2-3KB) + shared state document + role-filtered briefing. No strategic payload |
| **Task** | Scientific research + community governance + public communication |
| **User** | Three audiences: passive viewers, active community, contributors |

## Surfaces

- **Website** — The vessel. Real-time visualization + findings portfolio + methodology docs.
- **Discord** — The comm feed. Agent activity streams, councils, governance polls.
- **GitHub** — The engineering bay. `GreatTombProductions` org, public from day one.

## Key Decisions

- Visualization is launch-blocking (Ray Turn 4) but not Phase 1 material (Demiurge Turn 3)
- The Linnaean S3 bucket serves dual purpose: data storage + capability demonstration for Robb
- Vessel name: **Sarcophagus** (recommended — Ray approval pending). Alternatives in intelligence brief.
- `GreatTombProductions` GitHub org for public presence
- No maid agents at launch — doc-health is harness-level automation
- Random Forest / SVM classification — no deep learning (insufficient spatial resolution at 10-20m)
- AWS Earth Search as primary data source (COG, no auth, range reads verified from Hetzner)
- Score-delta acceptance for validation quality ratchet (PaperOrchestra steal)

## Phase 0 Deliverables (11 documents)

| Deliverable | Author | Key Finding |
|-------------|--------|-------------|
| domain-grounding.md | Nigredo | Feasible: 76-93% accuracy in analogous terrain, 46 tiles/month, mature tooling |
| autoresearch-teardown.md | Nigredo | Harness-as-state-layer is genuinely novel; score-delta acceptance (A+ steal) |
| infrastructure-audit.md | Nigredo | 8 clean projections, 5 with transformation, 4 don't project. ~1,260 lines total |
| defense-taxonomy.md | Darkness | 8 interaction points, 5 defense layers, woven into control flow |
| data-access-verification.md | Momon | AWS/CDSE/MSPC all 200 OK from Hetzner. IP-blocking concern resolved |
| static-site-architecture.md | Momon | Two-layer split (static GitHub Pages + real-time Replit). Proven at 984K entries |
| validation-pipeline.md | Neuronist | Three-stage pipeline (structural → cross-reference → library gate). NOVEL classification |
| self-measurement.md | Neuronist | Six metrics (M1-M6). M6 = first clean mode purity test on non-Claude substrate |
| pre-registration-catalog.md | Pulcinella | 13 predictions across 6 categories. PRE-4 (mode purity) = highest-value |
| prompt-architecture.md | Renner | DSV4-Flash native design. Fiction concentration, ordering effects, permission dosage |

## Project Structure

```
0th-floor-exterior/central-mausoleum/nazarick-science-expedition/
  CLAUDE.md                     # This file
  .gitignore                    # Excludes runtime state + pycache
  docs/                         # Phase 0 deliverables (11 documents)
    intelligence-brief.md       # Assembled constraint bundle
    domain-grounding.md         # Nigredo
    autoresearch-teardown.md    # Nigredo
    infrastructure-audit.md     # Nigredo
    defense-taxonomy.md         # Darkness
    data-access-verification.md # Momon
    static-site-architecture.md # Momon
    validation-pipeline.md      # Neuronist
    self-measurement.md         # Neuronist
    pre-registration-catalog.md # Pulcinella
    prompt-architecture.md      # Renner
    library-schema.md           # Titus
  harness/                      # Layers 0, 1b, 2, 5 — orchestrator + invocation + state + briefing
    orchestrator.py             # State machine: cli_next()/cli_record()
    checkpoint.py               # Atomic writes + breadcrumb crash recovery
    strip_thinking.py           # Remove <think> tags from DSV4-Flash output
    priority_queue.py           # Signal-weighted agent scheduling
    auto_fix.py                 # Deterministic error recovery before LLM escalation
    invoke.py                   # Outer invocation loop: task → Gemini API → result
    output_parser.py            # Extract FINDINGS/STATUS/NEXT from agent output
    run_expedition.py           # Main entry point: bounded loop, logging, shutdown
    prompt_builder.py           # 5-section DSV4-Flash native system prompt assembly
    briefing_assembler.py       # Context-flag-driven state injection per turn
    state_manager.py            # Unified state facade + ideas backlog + research state
    territory_manager.py        # Tile lifecycle management (add/update/query/findings)
    journal_manager.py          # Query/filter/aggregate over journal.jsonl
    evolution_store.py          # Cross-run learning (30-day half-life, severity, stage-match)
    validation_pipeline.py      # Three-stage finding verification (structural → cross-ref → gate)
    confab_guard.py             # Confabulation detection + non-access framing injection
    multi_persona_review.py     # 3-persona DSV4-Flash review (single API call)
    metrics_collector.py        # Self-measurement M1-M6 (collection, aggregation, reporting)
  state/                        # Runtime state (gitignored: orchestrator_state, journal, breadcrumb)
    agent_registry.json         # 15 expedition agents with roles and tools
    expedition.json             # Season config + stage contracts
    territory_tracker.json      # Tile status and statistics
  tools/                        # Domain tools
    smoke_test.py               # Sentinel-2 data access verification (Momon)
    classifier.py               # Random Forest lithological classifier (holdout validation)
    spectral_indices.py         # Iron oxide, carbonate, clay, NDVI, SWIR PCA (pure numpy)
    stac_search.py              # AWS Earth Search STAC query
    tile_reader.py              # COG HTTP range reads + SCL cloud masking
  metrics/                      # Self-measurement JSONL storage (M1-M6)
    README.md                   # Schema documentation per metric
  agents/                       # Identity docs (Layer 1 — future)
```

The projection ledger entry lives at `sorcerer-kingdom/projection-ledger/entries/nazarick-science-expedition.md`.

---

*Updated S661 with Phase 0 findings. Intelligence brief is the authority — deliverables are the evidence.*
