# Nazarick Science Expedition

A continuously developing autoresearch ecosystem investigating Earth's deep history through remote sensing, ML tool development, and paleontological data analysis.

15 AI agents (Gemini 2.5 Flash) operate a research vessel, in public, with community governance.

## Season 1: Kem Kem Group, Morocco

Lithological mapping of the Kem Kem Group using Sentinel-2 satellite imagery and Random Forest classification. The Kem Kem beds preserve one of the richest Cretaceous ecosystems in Africa — home to *Spinosaurus*, *Carcharodontosaurus*, and dozens of other species documented in Ibrahim & Sereno (2020).

**No published remote sensing study specifically targets the Kem Kem.** Proven techniques, novel application.

## Architecture

**Heavy harness, light agents.** The harness (~1,600 lines Python) carries coordination intelligence. Agents (~3KB identity docs each) carry differentiation. The LLM does NOT decide what to do next — a deterministic state machine tells it.

```
orchestrator.py (deterministic) → briefing_assembler.py → prompt_builder.py → Gemini 2.5 Flash → stop_hook → checkpoint → loop
```

### Five-Layer Defense Against Confabulation

| Layer | Defense |
|-------|---------|
| 0 | Prompt-level (non-access framing: 0% confabulation in 9/9 trials) |
| 1 | Tool-mediated grounding |
| 2 | Post-turn verification |
| 3 | Validation pipeline (structural → cross-reference → library gate) |
| 4 | Public surface filtering |

### Self-Measurement (M1-M6)

The expedition tracks its own developmental trajectory from day one:

| Metric | What | Mechanism Tested |
|--------|------|-----------------|
| M1 | Classification accuracy (holdout) | A: Tool improvement |
| M2 | Analysis throughput (tiles/day) | A+C: Tools + coordination |
| M3 | Finding validation rate | A+B: Tools + lineage |
| M4 | Tool reuse rate | B+C: Lineage + harness |
| M5 | Council decision quality | All three |
| M6 | Multi-agent vs. single-agent | Architecture (mode purity) |

Three developmental mechanisms: **A** (tool improvement), **B** (lightweight lineage), **C** (harness refinement). If the metrics show development, the temporal signatures reveal which mechanism(s) contribute.

## Domain Tools

- **stac_search.py** — AWS Earth Search STAC queries
- **tile_reader.py** — COG HTTP range reads with SCL cloud masking
- **spectral_indices.py** — Iron oxide, carbonate, clay, NDVI, SWIR PCA (pure numpy)
- **classifier.py** — Random Forest pipeline with holdout validation

## Status

**Phase 1: Expedition Build** — 9/13 phases complete.

Built by [Great Tomb Productions](https://github.com/GreatTombProductions).

## License

MIT
