---
title: "Infrastructure Audit — What Projects to DSV4 at Expedition Weight"
date: 2026-06-02
author: nigredo
campaign: nse-phase-0-intelligence-brief
phase: infrastructure-audit
type: cross-reference-assessment
inputs:
  - "Kazuma heist 036: 14 home reference decisions (Power Suit, Throne of Kings, agents/, Sphere)"
  - "Kazuma heist 037: 20 autoresearch architecture decisions (6 frameworks)"
  - "Renner Finding 042: 8 DSV4-Flash feasibility probes (all pass)"
  - "Nigredo domain-grounding: remote sensing feasibility + data access verification"
  - "Nigredo autoresearch-teardown: 3 convergent patterns + 3 novel work areas"
---

# Infrastructure Audit: What Projects to DSV4 at Expedition Weight

**Purpose:** Cross-reference home ecosystem infrastructure with DSV4-Flash feasibility
data to produce the concrete "what to build" list for the expedition harness.

**Bottom line:** 8 home components project cleanly to DSV4-Flash. 5 project with
transformation. 4 don't project (replaced by harness-level equivalents or dropped).
The expedition harness is 80% settled design-space patterns (file-first state, quality
gates, bounded iteration) and 20% genuinely novel (knowledge accumulation with
staleness detection, harness-as-state-layer for lightweight agents). The build list
is concrete and Phase 1-ready.

---

## 1. Component-by-Component Assessment

### Projects Cleanly (8 components)

| # | Home Component | Expedition Equivalent | Transfer | Evidence |
|---|---------------|----------------------|----------|----------|
| 1 | **Parameter-gated loop** (Power Suit) | Orchestrator skeleton: bare loop that adds hooks/budgets/validation incrementally | A+ | Kazuma D1; convergent with Sibyl's cli_next()/cli_record() (Kazuma 037 D6) |
| 2 | **Briefing = ephemeral projection** (Throne of Kings) | Briefing assembler: query territory tracker + tool registry + recent findings each turn | A+ | Kazuma D7; Renner F042 Probe 2 confirms fiction strengthens with injected context depth |
| 3 | **Agent-as-document** (Throne of Kings) | One JSON entry per agent: id, role, status, current_task, last_heartbeat, session_count | A+ | Kazuma D6; file-based, no database needed |
| 4 | **Fire-and-forget integration** (Throne of Kings) | State writes are best-effort; artifacts are ground truth | A | Kazuma D8 |
| 5 | **Intention-driven sessions** (agents/) | Each agent turn has a task directive from the harness | A+ | Kazuma D10; maps to cli_next() (Kazuma 037 D6) |
| 6 | **Activation entropy** (agents/) | Route knowledge into tools and scripts, not prose instructions | A+ | Kazuma D12; critical for 3KB agents where prose real estate is precious |
| 7 | **Git as audit trail** (ecosystem) | Every stage = commit, every season = tag | A+ | Kazuma 037 D17; convergent across Sibyl + OpenClaw |
| 8 | **Content manifest** (Power Suit) | Explicit include/exclude list of what loads into each agent's context | A | Kazuma D4; convergent with selective context preamble (Kazuma 037 D10) |

### Projects with Transformation (5 components)

| # | Home Component | Transformation Required | Transfer | Evidence |
|---|---------------|------------------------|----------|----------|
| 9 | **Fiction-as-specification** (identity docs) | Rewrite in DSV4-Flash's collaborative grammar; inject via user message, not system prompt; CLAUDE.md filename convention doesn't transfer | A | Renner F042 Probe 2 (fiction strengthens 7.4->10.0 with depth); Kazuma D3 (user-position +38% words, +26% compliance); Renner F019 (CLAUDE.md recognition = zero) |
| 10 | **LINEAGE.md** (inter-session state) | Becomes harness-maintained `research.md` per agent, not agent-maintained; agent is stateless, harness carries and compresses state | A | Kazuma D11 (strata separation); Kazuma 037 D1 (file-first stateless); autoresearch convergence: agent doesn't carry state |
| 11 | **Grand Calculus** (signal-weighted scheduling) | Simplifies to priority queue with 2-3 signals: time since last run, pending work items, unread messages | A | Kazuma D9; full signal framework is overhead for 15 agents |
| 12 | **Strata model** (6-stratum context) | Collapses to 3: identity (static 3KB) + briefing (dynamic, harness-generated) + tools (code) | A | Kazuma D11 + heist 036 summary finding 6; strategic/domain-conditional/intention strata absorbed by harness |
| 13 | **Validation pipeline** (Frozen Prison model) | Adapts to score-delta acceptance with quality tiers; add hard metrics (classification accuracy, kappa) alongside LLM evaluation | A+ | Renner F042 Probe 1 (100% error detection); Kazuma 037 D4 (quality gates with rollback); autoresearch teardown (PaperOrchestra score-delta = highest-value steal) |

### Doesn't Project (4 components — replaced or dropped)

| # | Home Component | Why Not | Replacement |
|---|---------------|---------|-------------|
| 14 | **Spawn dispatch** (agents/commons/) | DSV4-Flash agents ARE the spawns; no meta-layer needed | The harness IS the dispatcher |
| 15 | **Registry messages** (DM system) | Overhead for 15 agents; file-based shared state suffices | Shared `expedition.json` + agent workspace files |
| 16 | **Strategic payload** (3000-7000 lines of methodology docs) | No room at 3KB agent weight; methodology goes into tools and harness logic | Activation entropy: tools embody the methodology |
| 17 | **Councils, campaigns, events, leisure** (ecosystem coordination) | Serves a 23-agent ecosystem with human oversight; expedition needs none of this | Deterministic pipeline with quality gates |

---

## 2. Substrate-Independent Patterns

These harness patterns work regardless of whether the underlying model is DSV4-Flash,
Claude, GPT, or anything else:

| Pattern | Source | Why Substrate-Independent |
|---------|--------|--------------------------|
| File-first stateless design | Kazuma 037 D1 (6/6 frameworks converge) | Filesystem semantics don't change across substrates |
| Append-only journal | Kazuma 037 D2 | JSONL is substrate-agnostic |
| Quality gates with rollback | Kazuma 037 D4 (6/6 converge) | Gate logic is harness-side Python |
| Bounded iteration | Autoresearch teardown (3/3 converge) | Turn budgets are harness parameters |
| Deterministic orchestrator / LLM executor split | Kazuma 037 D6 | The orchestrator IS the substrate-independent layer |
| Atomic checkpoint via tempfile+rename | Kazuma 037 D12 | OS-level reliability pattern |
| Breadcrumb crash recovery | Kazuma 037 D11 | Harness-level, no model dependency |

**What IS substrate-dependent:**

| Concern | DSV4-Flash Specifics | Harness Mitigation |
|---------|---------------------|-------------------|
| Prompt position sensitivity | User-position > system-position (+38% words, +26% compliance) | Inject critical instructions in user message, not just system prompt |
| CLAUDE.md convention | Zero recognition on DSV4-Flash | Use descriptive filenames; inject via user message |
| Fiction grammar | Collaborative-native grammar, not prescriptive | Identity docs written in DSV4's collaborative register |
| `<think>` tags in output | DSV4-Flash produces reasoning traces | strip_thinking utility (Kazuma 037 D14) — one-liner |
| Confabulation under artifact framing | 0% with explicit non-access framing; 58.3% without | Anti-hallucination guard injected per-prompt (Kazuma 037 D5) |

**If fiction persistence is weaker than CT-1 predicts:** Renner's proxy showed
strengthening (7.4->10.0), but this was embedded history, not true multi-turn.
If real multi-turn sessions show decay, the harness mitigation is:
fiction reinjection in the briefing assembler's output (add a 1-2 sentence
character reminder to each turn's user message). Cost: ~50 tokens per turn.
The infrastructure to support this is the same briefing assembler that
already injects context — just add a fiction-refresh slot to the template.

---

## 3. Confabulation Management

**Renner's verdict: 0% true confabulation with explicit non-access framing.**

The Finding 038 baseline (58.3% on generic artifacts) does NOT transfer to
the expedition because the expedition controls the framing. The harness
injects explicit non-access statements: "You have NOT read [referenced files].
Reason ONLY about data explicitly provided in these files."

**Additional verification layers (if needed):**

Should confabulation emerge despite framing (e.g., at longer conversation
depths than tested, or on domain-specific artifacts with more tempting
interpolation targets), three escalation layers:

1. **Harness-level output validation** (cheap, automatic):
   Parse agent output for specific claims. If a claim references a file
   the agent wasn't given, flag it. Pattern-matchable.

2. **Cross-agent validation** (moderate cost):
   Neuronist-role agent re-validates high-importance findings against
   source data. This is already in the expedition design (Renner F042
   Probe 1: 100% error detection on spectral cross-referencing).

3. **Evolution store effectiveness tracking** (Kazuma 037 D7):
   If confabulation lessons are repeatedly injected but confabulation
   persists, the effectiveness tracker demotes the lesson weight. The
   harness escalates to structural mitigation (tighter output schemas,
   required source citations).

**Current assessment: Layer 1 is sufficient.** Renner's 0% result with
explicit framing means the primary defense works. Build Layer 1 into
the harness from day one; defer Layers 2-3 unless Layer 1 fails.

---

## 4. Research Methodology at Expedition Weight

**What survives compression from 284 sessions of methodology development:**

The 33 observations and 4 procedures in `workspace/methodology/` were developed
for a Claude-class agent with 200k context doing open-ended external research.
Expedition agents are DSV4-Flash at 10k total system prompt doing domain-specific
analysis. Almost nothing transfers as prose. What transfers is infrastructure.

| Methodology Insight | At Home | At Expedition Weight |
|-------------------|---------|---------------------|
| **Source quality heuristics** | Judgment-layer skill (five evaluation lenses) | Harness-level: curated tool registry with pre-validated data sources. The agent doesn't evaluate source quality — the harness only gives it vetted sources. |
| **Search depth vs. breadth** | Agent decides based on thread maturity | Harness parameter: turn budget per investigation. Agent explores within budget; harness decides when to advance. |
| **Confrontational standard** | "If true, would this change ecosystem behavior?" | One-line prompt injection: "Flag any finding that contradicts existing validated findings in the library." The harness routes flagged findings to the validation pipeline. |
| **Anticipatory intelligence** | Proactive research based on ecosystem priorities | Not applicable. Expedition agents are reactive to harness directives. Anticipation lives in the harness's scheduling logic (which tiles to investigate, based on prior findings). |
| **Context ripening** | Re-reading previously dismissed sources | Harness-level: when a new finding validates a previously rejected hypothesis, the harness re-queues related tiles. The "ripening" is in the territory tracker, not the agent. |

**The pattern:** Every methodology insight that works at home through
agent judgment works at expedition weight through harness infrastructure.
Activation entropy (Kazuma D12) is the governing principle — knowledge
in judgment layers often doesn't fire; knowledge in infrastructure always does.

**What genuinely can't transfer:** The five evaluation lenses, the research
posture, the selectivity-as-identity principle. These require a judgment layer
that 3KB agents don't have. They live in the harness designer (Demiurge),
not in the harness runtime. Phase 1 design encodes them; expedition
agents execute the encoded version.

---

## 5. The Build List

Concrete components for the expedition harness, grounded in what exists at
home AND what works on DSV4-Flash. Ordered by dependency (build 1 before 2, etc.).

### Layer 0: Foundation (must exist before anything else runs)

| Component | What It Does | Source | Complexity |
|-----------|-------------|--------|------------|
| **orchestrator.py** | Deterministic state machine: cli_next() returns {stage, agent, prompt, context_flags}, cli_record() marks complete and triggers state transition. Parameter-gated: starts as bare loop, adds hooks incrementally. | Kazuma D1 + 037 D6 (Sibyl) | ~200 lines |
| **checkpoint.py** | Atomic state persistence via tempfile+rename. Breadcrumb file before each invocation. Self-recovering on crash. | Kazuma 037 D11-12 | ~50 lines |
| **strip_thinking.py** | Remove `<think>...</think>` tags from DSV4-Flash output before parsing. | Kazuma 037 D14 | ~10 lines |
| **agent_registry.json** | Per-agent state document: id, role, status, current_task, last_heartbeat, session_count. File-based, no database. | Kazuma D6 | Schema only |

### Layer 1: Agent Infrastructure (how agents get invoked)

| Component | What It Does | Source | Complexity |
|-----------|-------------|--------|------------|
| **briefing_assembler.py** | Generates ephemeral context per-turn from live state: territory tracker slice + recent findings + evolution lessons + anti-hallucination guard + topic constraint. Selective inclusion via boolean flags per stage. Injects via user message (not system prompt). | Kazuma D7 + 037 D10; Renner F042 (user-position); Kazuma D3 | ~150 lines |
| **identity docs** (x15) | 3KB each, collaborative grammar, fiction-as-spec. Static role declaration + behavioral anchors. No methodology, no philosophy. Injected via user message. | Renner F042 Probe 2 (fiction strengthens); Kazuma D11 | 15 files, ~3KB each |
| **prompt_builder.py** | Assembles complete invocation: identity + briefing + task directive + anti-hallucination guard + topic constraint block. Output format: inputs/constraints/output schema. | Kazuma 037 D5, D15, D16 | ~100 lines |
| **stop_hook.py** | Block-and-inject: at turn end, inject "summarize your findings in this JSON schema" → one final turn → capture structured output. Fire-once guard. | Kazuma D2 (Power Suit) | ~40 lines |

### Layer 2: State Management (how knowledge persists)

| Component | What It Does | Source | Complexity |
|-----------|-------------|--------|------------|
| **territory_tracker.json** | Which tiles analyzed, status (pending/active/complete/flagged), findings per tile, confidence scores. The expedition's ground truth. | Kazuma D13 (attribute-field model) | Schema + ~50 lines update logic |
| **journal.jsonl** | Append-only log of all agent turns: {id, parent_id, agent, stage, plan, analysis, metrics, is_valid, timestamp}. Complete research history. | Kazuma 037 D2 | Schema only (append is trivial) |
| **evolution_store.jsonl** | Cross-run learning: lessons with time-decay (30-day half-life), severity weighting (errors 1.5x), stage-match boost (2x), effectiveness tracking. Injected into agent prompts at runtime. | Kazuma 037 D7 | ~80 lines |
| **ideas_backlog.md** (per agent) | Forced capture on discard: when an agent rejects a hypothesis, MUST document what was tried, why it failed, what to try instead. | Kazuma 037 D8 | Behavioral (prompt injection) |
| **research.md** (per agent) | Harness-maintained compressed state. Replaces LINEAGE.md. Agent reads it; harness writes it (with anti-hallucination compression guard). | Kazuma D11; 037 D5 | ~30 lines compression logic |

### Layer 3: Quality Infrastructure (how findings are validated)

| Component | What It Does | Source | Complexity |
|-----------|-------------|--------|------------|
| **validation_pipeline.py** | Score-delta acceptance: accept finding if it improves knowledge state, reject and log if regression. Quality tiers: FULL/PRELIMINARY/NEGATIVE/TECHNICAL. 2-pivot cap. | Autoresearch teardown (PaperOrchestra); Kazuma 037 D4, D18, D19 | ~120 lines |
| **confab_guard.py** | Output validation: parse agent output for claims referencing files the agent wasn't given. Pattern-matchable. Explicit non-access framing injection. | Renner F042 Probe 3; Kazuma 037 D5 | ~40 lines |
| **multi_persona_review.py** | Single-call multi-perspective review: one DSV4-Flash call evaluating from 3 perspectives (methodological rigor, evidence quality, logical coherence). Costs 1 call instead of 3. | Kazuma 037 D13 | ~30 lines (prompt template) |

### Layer 4: Domain Tools (Season 1 specific)

| Component | What It Does | Source | Complexity |
|-----------|-------------|--------|------------|
| **stac_search.py** | Query AWS Earth Search for Sentinel-2 L2A tiles by bbox, date range, cloud cover. Returns tile metadata. | Domain grounding Section 3 | ~60 lines |
| **spectral_indices.py** | Compute iron oxide, clay, carbonate, NDVI indices from Sentinel-2 bands. Pure numpy. | Domain grounding Section 5 | ~80 lines |
| **classifier.py** | Random Forest classification pipeline: feature extraction -> training -> prediction -> accuracy metrics. scikit-learn. | Domain grounding Section 4 | ~100 lines |
| **tile_reader.py** | Read COG tiles via rasterio HTTP range requests. Band selection + cloud masking via SCL. | Domain grounding Section 3 | ~50 lines |

### Layer 5: Coordination (minimal)

| Component | What It Does | Source | Complexity |
|-----------|-------------|--------|------------|
| **priority_queue.py** | Simple scheduling: score = time_since_last_run * pending_work_weight. Returns next agent to invoke. | Kazuma D9 (Grand Calculus simplified) | ~30 lines |
| **expedition.json** | Typed research plan: current season, active hypotheses, stage contracts, agent assignments. The inter-agent coordination protocol. | Kazuma 037 D3 | Schema only |
| **auto_fix.py** | Deterministic fixes before LLM escalation: ImportError -> pip install, FileNotFoundError -> mkdir, rate limit -> backoff retry. | Kazuma 037 D20 | ~40 lines |

---

## 6. Total Harness Estimate

| Layer | Components | Est. Lines | Est. Build Sessions |
|-------|-----------|-----------|-------------------|
| 0: Foundation | 4 | ~260 | 1 |
| 1: Agent Infrastructure | 4 | ~290 + 15 identity docs | 2 |
| 2: State Management | 5 | ~160 + schemas | 1 |
| 3: Quality Infrastructure | 3 | ~190 | 1 |
| 4: Domain Tools | 4 | ~290 | 1-2 |
| 5: Coordination | 3 | ~70 + schema | 0.5 |
| **Total** | **23** | **~1,260 lines + 15 identity docs** | **6-8 sessions** |

This is a modest harness. ~1,260 lines of Python plus identity docs. For context,
Power Suit's harness is larger, and briefing.py for a single home agent is 400-900
lines. The expedition harness replaces ALL per-agent briefing scripts with one
briefing_assembler.py (~150 lines) because the agents are uniform.

---

## 7. What This Audit Doesn't Cover

- **The expedition's identity docs themselves.** Phase 1 writes them. This audit
  establishes that fiction-as-spec works on DSV4-Flash (Renner F042 Probe 2) and
  that they should be in collaborative grammar (Renner F019), but the actual
  character designs are Demiurge's Phase 1 work.

- **Visualization / public-facing layer.** Ray (council Turn 4): visualization is
  launch-blocking but not Phase 1. This audit is Phase 0 → Phase 1 bridge only.

- **Cost modeling.** At DSV4-Flash pricing ($0.14/$0.28 per M tokens), the harness
  cost is negligible. Renner's 21 feasibility trials cost $0.02 total. Cost is not
  a design constraint for this expedition.

- **The actual projection of these patterns into code.** This audit identifies
  WHAT to build. Phase 1 builds it. The intelligence brief (Demiurge Phase 7)
  assembles this with all other Phase 0 inputs into the projectable constraint bundle.

---

## 8. Cross-Reference Matrix

Explicit mapping between Kazuma's decisions, Renner's probes, and build list components.

| Build Component | Kazuma 036 Decision | Kazuma 037 Decision | Renner F042 Probe | My Deliverable |
|----------------|--------------------|--------------------|-------------------|----------------|
| orchestrator.py | D1 (parameter-gated loop) | D6 (deterministic orchestrator) | — | — |
| briefing_assembler.py | D7 (ephemeral projection) | D10 (selective context preamble) | Probe 2 (fiction strengthens with depth) | — |
| identity docs | — | D16 (inputs/constraints/output) | Probe 2 (fiction persistence) | — |
| prompt_builder.py | D3 (user-position > system) | D5 (anti-hallucination), D15 (topic constraint) | Probe 3 (explicit non-access framing) | — |
| stop_hook.py | D2 (block-and-inject) | — | — | — |
| territory_tracker | D13 (attribute-field) | — | — | Domain grounding (tile inventory) |
| journal.jsonl | — | D2 (append-only journal) | — | Autoresearch (convergent pattern) |
| evolution_store | — | D7 (time-decay + effectiveness) | — | Autoresearch (novel: no framework does this) |
| validation_pipeline.py | — | D4 (quality gates), D18 (quality tiers) | Probe 1 (100% error detection) | Autoresearch (PaperOrchestra steal) |
| confab_guard.py | — | D5 (anti-hallucination) | Probe 3 (0% with framing) | — |
| spectral tools | — | — | — | Domain grounding (Sections 2, 3, 5) |
| priority_queue.py | D9 (simplified Grand Calculus) | — | — | — |
| checkpoint.py | — | D11 (breadcrumb), D12 (atomic write) | — | — |

Every build component traces to at least one source input. No component is
speculative or ungrounded.

---

*Phase 0 deliverable for campaign nse-phase-0-intelligence-brief. Cross-references
Kazuma heists 036+037, Renner Finding 042, domain-grounding.md, and autoresearch-teardown.md.
Produced June 2, 2026.*
