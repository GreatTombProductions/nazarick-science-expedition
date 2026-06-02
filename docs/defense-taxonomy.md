# Orchestrator Defense Layer Taxonomy

*Phase 0 deliverable. Every interaction point where agent output touches persistent state, classified by failure mode risk, with the defense mechanism each requires.*

*Author: Darkness (S130, post-council 2c37ddfe)*
*Inputs: Council Turn 18, Cocytus DM (Renner Finding 042 correction), Kazuma Heist 037 (20 autoresearch decisions from 6 sources), Cocytus Turn 10 (state management), Neuronist Turn 13 (validation architecture), Yuri Turn 17 (decay profiles)*

---

## Design Principle

**The orchestrator is the Crusader.** It stands between agent output and persistent state. Every agent output passes through it. Its job is to absorb the hits — confabulated state, stale references, unvalidated claims, format violations, tool invocation failures — so that none reach the surfaces where they'd cause damage.

**STATE heavy, BEHAVIOR light.** The system prompt should be heavy on what's true right now and light on how to act. DSV4-Flash already knows how to act under fiction-as-spec framing with tool access. Behavioral instructions at expedition weight are mostly masking, not protecting.

**Subtractive first, then additive.** Design the defense layer (what agents CAN'T do wrong) before the identity docs (what agents SHOULD do right). The identity docs become lighter because the harness is heavier.

---

## Priority Stack (Revised Per Renner Finding 042)

Cocytus's post-council DM reported that Renner Finding 042 Probe 3 shows **0% true confabulation** when using explicit non-access framing ("you have NOT read [referenced files]"). This dramatically changes the defense layer priority ordering from the council's initial 58.3% baseline.

| Priority | Mechanism | What It Prevents | Cost | Effectiveness |
|----------|-----------|-----------------|------|---------------|
| **1** | Explicit non-access framing | Confabulated artifact content | Zero — prompt text only | 0% confab (Finding 042) |
| **2** | Tool-mediated state queries | Confabulated state claims | Low — tool implementation | 100% grounded (tool output is real) |
| **3** | Post-turn artifact verification | False completion claims | Low — file existence checks | Deterministic |
| **4** | Validation gate | Unverified findings in library | Moderate — pipeline stage | Deterministic |
| **5** | Staleness detection | Yuri's T-1 decay | Low — timestamp comparisons | Deterministic |
| **6** | Duplicate work detection | Repetition loop | Low — tracker lookups | Deterministic |

Priority 1 is the discovery: explicit framing eliminates the dominant confabulation risk at zero cost. Priorities 2-6 are structural defenses for different failure modes that persist regardless of confabulation rate.

---

## Interaction Points: Complete Catalog

Every place where agent output touches persistent state, what can go wrong, and what prevents it.

### IP-1: Agent Claims About Territory Status

**What happens:** Agent reads territory tracker, reasons about tile status, reports "tile T29RNR classified" or "all tiles in sector 7 complete."

**Failure modes:**
- **Confabulated status (CRITICAL → MITIGATED).** Agent generates plausible but fabricated claims about tile states. Previously the dominant risk at 58.3% baseline. Now mitigated to ~0% by explicit non-access framing.
- **Stale status.** Agent reads tracker that hasn't been updated since last pipeline completion. Reports outdated state.
- **Aggregation error.** Agent correctly reads individual tile statuses but incorrectly summarizes ("all complete" when 287/623 are complete).

**Defense mechanisms:**
1. **Explicit non-access framing (P1).** System prompt includes: "You have NOT read the territory tracker. Use the `territory-status` tool to query current state." The framing prevents the agent from generating tracker content from its training distribution.
2. **Tool-mediated query (P2).** `territory-status --tile T29RNR` returns ground truth from the tracker file. `territory-status --sector 7 --summary` returns aggregated counts. Agent calls tools, gets real answers.
3. **Post-turn verification (P3).** When agent claims "tile T29RNR classified," the post-turn function checks: does `findings/T29RNR-classification.json` exist? If not, the claim doesn't propagate.

**Autoresearch pattern (Kazuma Decision 6):** The deterministic orchestrator tells the agent which tiles to work on. The agent doesn't need to query territory status to decide — the harness decided for it. This eliminates the aggregation error class entirely.

---

### IP-2: Agent Writes to Shared State Store

**What happens:** Agent produces findings, status updates, or tool outputs that the post-turn function extracts and writes to the shared state store.

**Failure modes:**
- **Partial write / crash mid-write.** Agent turn crashes after partial output. Post-turn extracts incomplete data. State store corrupted.
- **Format violation.** Agent produces output that doesn't match the expected structure. Parser fails silently or extracts garbage.
- **Conflicting writes.** Two agent turns complete near-simultaneously and write conflicting state. (Less likely with sequential turn management, but possible with parallel infrastructure agents.)

**Defense mechanisms:**
1. **Atomic checkpoint writes (Kazuma Decision 12).** All state store writes use tempfile+rename: `mkstemp() → write → Path.replace()`. If the write crashes, the previous state survives intact. One-time implementation, permanent reliability.
2. **Breadcrumb pattern (Kazuma Decision 11).** Before each agent invocation, the harness writes `breadcrumb.json`: `{agent, stage, started_at, expected_output_files}`. If the agent crashes, the harness reads the breadcrumb and knows exactly what to retry. Combined with atomic writes, this makes the system self-recovering.
3. **Structured extraction with fallback.** The post-turn function attempts to parse structured output (JSON tool outputs, structured finding format). If parsing fails, falls back to raw text storage with a `format: "unstructured"` flag. Degrade gracefully, never crash. Every edge case absorbed.
4. **Sequential turn management.** One agent active at a time for state-writing operations. Infrastructure agents (pipeline monitoring, tool registry updates) can run in parallel only if they write to non-overlapping state partitions.

**Autoresearch pattern (Kazuma Decision 3):** Structured JSON schemas as inter-agent contracts. Each stage has a `StageContract` with `input_files`, `output_files`, and definition of done. The contract IS the format validation — output that doesn't match the contract doesn't advance the pipeline.

---

### IP-3: Findings Enter the Library

**What happens:** Agent analysis produces a finding ("laterite exposure detected at coordinates X with confidence Y"). The finding passes through the validation pipeline and enters the expedition library.

**Failure modes:**
- **Echo chamber.** Agent generates finding, validator confirms without genuine cross-reference, finding enters library as "verified" when it's actually unfounded. The council's identified pathological basin.
- **Stale tool versioning.** Finding is valid against classifier v1. Classifier retrains to v2. Finding remains in library referencing v1 results. Future agents build on potentially invalidated findings.
- **Missing provenance.** Finding enters library without recording which tools, reference data, and analysis steps produced it. Future agents can't evaluate or reproduce the finding.

**Defense mechanisms:**
1. **Validation gate (P4).** Architectural constraint: analysis output CANNOT enter the library without passing through a validation stage. The pipeline refuses to advance unvalidated findings. Not a behavioral rule — a pipeline stage that deterministically gates library entry.
2. **Structured finding format (Titus's schema).** Every library finding carries: claim, evidence (method, tool_version, confidence, reference_data), location, validation status, supersession chain, retrieval hints. The format enforces provenance by making it a required field, not an optional annotation.
3. **Quality tier model (Kazuma Decision 18).** Findings tier into: STRONG (multi-evidence, cross-referenced), PRELIMINARY (single-source, limited validation), NEGATIVE (valid null result), TECHNICAL (infrastructure observation). Tier determines visibility on public surfaces. PRELIMINARY findings are in the library but flagged — they don't appear in the public portfolio or weekly synthesis until promoted.
4. **Tool version tracking.** Every finding records the tool version that produced it. When a tool retrains, the harness can sweep existing findings and flag those produced by superseded tools. Not automatic re-validation — but automatic staleness detection.
5. **Anti-hallucination guard on validation (Kazuma Decision 5).** The validation agent's prompt includes: "You MUST reason only about data explicitly provided in these files. Do not invent measurements, cite papers you haven't been given, or claim prior findings not documented in the journal." Shared prompt fragment injected into all agent system prompts.

**Autoresearch pattern (Kazuma Decision 4):** Quality gates with rollback and ratchet. If a finding contradicts established findings at higher confidence, the new finding gets flagged, not the established one. Quality can't decrease through the validation pipeline.

---

### IP-4: Agent Updates Tool Registry

**What happens:** Aura-expedition deploys a new tool or updates an existing one. The tool registry YAML needs to reflect the change so other agents can discover and use the new capability.

**Failure modes:**
- **Phantom integration (Yuri).** Tool exists in code but not in registry. Agents don't know it's available. Or: tool is in registry but broken/removed. Agents call a ghost.
- **Stale invocation syntax.** Tool adds a new `--format` flag. Registry still shows old syntax. Agents call tools with outdated arguments.
- **Capability mismatch.** Registry describes capabilities the tool doesn't actually have (e.g., "supports GeoTIFF output" when it only supports JSON).

**Defense mechanisms:**
1. **Registry-as-deployment-artifact.** The tool registry update is part of the tool deployment process, not a separate manual step. When a new tool is deployed, the deployment script writes the registry entry. When a tool is updated, the deployment script updates the registry entry. Atomic — the tool and its registry entry ship together.
2. **End-to-end health check (P5).** On each heartbeat cycle, the harness runs a canary invocation of each registered tool: call with minimal valid input, verify output format matches registry description. If the canary fails, the tool is marked `status: degraded` in the registry and excluded from briefing injection until fixed.
3. **Explicit non-access framing on registry.** "You have NOT memorized the tool list. Use `tool-list` to see available tools." Prevents agents from confabulating tool names or capabilities from their training distribution. The tool-list command reads the live registry.

---

### IP-5: Agent Output Streams to Discord

**What happens:** Agent reasoning is streamed to Discord at human reading speed. The audience watches agents think.

**Failure modes:**
- **Confabulated citations.** Agent references papers, datasets, or prior findings that don't exist. The audience has no way to verify in real time. Credibility damage.
- **Confident false claims.** Agent asserts a geological interpretation with confidence but no supporting evidence in the current context. Reads as authoritative to non-expert audience.
- **State leakage.** Agent's reasoning reveals infrastructure details, error states, or debugging information that breaks the vessel fiction.

**Defense mechanisms:**
1. **Pre-stream filtering.** The streaming pipeline filters agent output before sending to Discord. Remove raw error traces, debugging output, and system-level state references. Replace with fiction-appropriate equivalents if needed ("instruments recalibrating" instead of "API rate limit hit").
2. **Citation verification (Kazuma Decision 5).** Agent prompts include: "Do not cite specific papers by name unless the paper was provided in your context. Use phrases like 'published research suggests' for general domain knowledge." This prevents confabulated citations without suppressing domain knowledge.
3. **Confidence calibration through fiction.** The fiction frame naturally calibrates this. Expedition agents are investigating unknown territory — uncertainty is the character's premise, not a weakness to hide. DSV4-Flash's exploratory hedging under high permission (Renner) produces naturally calibrated output: "the spectral signature is consistent with laterite, but we should cross-reference with the published geological map" rather than "this is laterite."
4. **Topic constraint block (Kazuma Decision 15).** Prevents agents from producing meta-commentary about their own process as if it were research content. "Your findings must directly address [current research question]. Do not discuss your own methodology as if it were a research contribution."

---

### IP-6: Agent Updates Research Journal

**What happens:** After each turn, the agent's work is logged to the append-only research journal (JSONL). The journal is the complete research history.

**Failure modes:**
- **Journal corruption.** Crash during append corrupts the JSONL file. All subsequent reads fail.
- **Missing entries.** Agent turn completes but journal append fails. Research history has gaps.
- **Bloated journal.** After months of operation, the journal exceeds what can be injected into agent context. Historical entries become inaccessible.

**Defense mechanisms:**
1. **Atomic append (Decision 12 adapted).** JSONL append via: read existing, write new temp file with appended entry, rename. Not as simple as file.append() but crash-safe.
2. **Journal as part of post-turn (not agent responsibility).** The agent doesn't write to the journal directly. The post-turn function extracts structured findings and appends to the journal. If the agent crashes, whatever it produced before crashing is still extracted. If it produced nothing, the journal entry records: `{status: "crashed", agent, stage, timestamp}`.
3. **Evolution store with time-decay (Kazuma Decision 7).** For cross-run learning injection, use exponential time-decay: `weight = exp(-age_days * ln(2) / 30)`. 30-day half-life, 90-day max age. The journal grows unbounded but the INJECTED journal is always bounded — recent entries weighted heavily, old entries fade.
4. **Forced idea capture on discard (Kazuma Decision 8).** When an agent determines a hypothesis is invalid or an analysis approach fails, the post-turn function records: what was tried, why it failed, and suggested alternatives. Knowledge accumulates even from failures.

---

### IP-7: Briefing Assembly (Harness → Agent)

**What happens:** Before each agent invocation, the harness assembles a briefing: identity + selective prior context + territory summary + evolution lessons + tool registry. This is the agent's entire world.

**Failure modes:**
- **Stale briefing content.** Briefing includes state that was true at assembly time but changed before the agent processes it. Agent acts on outdated information.
- **Context overflow.** Briefing exceeds DSV4-Flash's effective context budget. Agent output degrades silently.
- **Missing context.** Briefing omits information the agent needs for its current task. Agent confabulates the missing context.

**Defense mechanisms:**
1. **Selective inclusion with boolean flags (Kazuma Decision 10).** Each stage declares what prior artifacts it needs. The hypothesis agent doesn't get raw data statistics. The pipeline agent doesn't get the full literature review. Selective inclusion keeps briefings within budget AND reduces confabulation surface — less irrelevant context means fewer opportunities to confabulate connections.
2. **Just-in-time assembly.** Briefing is assembled immediately before the agent invocation, not pre-cached. State reads happen at assembly time. This minimizes the staleness window to the duration of the agent turn itself.
3. **Context budget tracking.** The briefing assembler tracks total token count and warns when approaching the budget ceiling. Truncation strategy: evolution lessons (oldest first) → journal entries (oldest first) → territory summary (compress to counts) → identity (never truncated). Priority: what the agent IS > what the agent KNOWS > what happened before.
4. **Explicit non-access framing for excluded context.** When the briefing OMITS context (e.g., hypothesis agent doesn't get pipeline status), the system prompt says so: "You have NOT been briefed on pipeline status. If you need pipeline information, use the `pipeline-status` tool." This prevents the agent from confabulating omitted context.

---

### IP-8: Public Surface Rendering (State → Website/Discord)

**What happens:** Internal state (territory tracker, findings library, tool registry) is rendered to public-facing surfaces. The audience consumes these as ground truth.

**Failure modes:**
- **T-1 staleness (Yuri).** Public surface shows state that's behind the internal state. Audience sees "tile T29RNR: queued" when it's already classified. The audience can't detect this.
- **Rendering divergence.** Internal state, Discord output, and website all show different things because they read from different sources or at different times.
- **Missing uncertainty indicators.** Public surfaces display findings without confidence levels or tool versioning. Non-expert audience treats preliminary findings as established facts.

**Defense mechanisms:**
1. **Single source of truth.** All public surfaces render from the same state store. The website doesn't maintain its own copy. Discord doesn't cache. Both read from the canonical state files.
2. **Provenance timestamps (Yuri).** Every rendered state includes: "Territory status as of 2026-07-15 14:32 UTC." The timestamp is the staleness signal that lets attentive audience members calibrate trust. Low cost, high option value.
3. **Quality tier visibility.** Public surfaces show finding tiers. STRONG findings appear in the portfolio. PRELIMINARY findings appear with explicit "preliminary" badge. NEGATIVE results appear in the expedition log. The audience sees the expedition's epistemological posture, not just its conclusions.
4. **Graceful degradation on orchestrator outage.** Static content (GitHub Pages) serves when the real-time layer (Replit) is offline. "Vessel currently in maintenance — last transmission [timestamp]" is acceptable and thematic.

---

## The Defense Stack (Layered Summary)

```
LAYER 0: PROMPT-LEVEL DEFENSE
├── Explicit non-access framing on all artifact references (0% confab — Finding 042)
├── Anti-hallucination guard: shared prompt fragment in all agent system prompts
├── Citation constraint: no paper names unless paper was provided in context
├── Topic constraint block: findings must address research question, not process
└── Confidence calibration: fiction frame makes uncertainty the natural register

LAYER 1: TOOL-MEDIATED GROUNDING
├── territory-status tool: ground truth from tracker file
├── tool-list tool: live registry, not memorized capabilities
├── pipeline-status tool: real pipeline state, not confabulated
└── finding-check tool: verify whether a finding exists before referencing it

LAYER 2: POST-TURN VERIFICATION
├── Artifact verification: check file exists before marking turn complete
├── Structured extraction with fallback: parse or degrade, never crash
├── Atomic writes: tempfile+rename on all state store updates
├── Breadcrumb pattern: crash recovery state written before each invocation
├── Journal append: post-turn function handles, not agent
└── Forced idea capture: failed hypotheses must produce documented alternatives

LAYER 3: PIPELINE GATES
├── Validation gate: analysis → validation → library (no bypass)
├── Quality tiers: STRONG/PRELIMINARY/NEGATIVE/TECHNICAL
├── Tool version tracking: findings carry tool version, sweep on retrain
├── Duplicate work detection: check tracker before assigning tile
└── Staleness detection: timestamp-based freshness checks on all state entries

LAYER 4: PUBLIC SURFACE DEFENSE
├── Single source of truth: all surfaces read same state store
├── Provenance timestamps on all rendered state
├── Quality tier visibility: audience sees epistemological posture
├── Pre-stream filtering: remove system-level details from Discord
└── Graceful degradation: static layer survives orchestrator outage
```

---

## Integration with Autoresearch Architecture

Kazuma's Heist 037 synthesized architecture uses the deterministic orchestrator / LLM executor split (Decision 6). The defense layer maps onto this architecture:

| Autoresearch Component | Defense Layer Responsibility |
|----------------------|---------------------------|
| `cli_next()` — harness tells agent what to do | Selective context inclusion (Layer 0), duplicate work prevention (Layer 3) |
| Agent execution | Anti-hallucination guard (Layer 0), tool-mediated grounding (Layer 1) |
| `cli_record()` — harness records completion | Artifact verification (Layer 2), atomic writes (Layer 2), breadcrumb cleanup (Layer 2) |
| `StageContract` validation | Format validation (Layer 2), quality gate enforcement (Layer 3) |
| Journal append | Post-turn extraction (Layer 2), forced idea capture (Layer 2) |
| Briefing assembly | Selective inclusion (Layer 0), just-in-time assembly, explicit non-access framing (Layer 0) |
| Discord streaming | Pre-stream filtering (Layer 4), citation constraint (Layer 0), topic constraint (Layer 0) |
| Public rendering | Single source of truth (Layer 4), provenance timestamps (Layer 4), quality tiers (Layer 4) |

The defense layer is NOT a separate system bolted onto the orchestrator. It's woven into the orchestrator's existing control flow. Every `cli_next()` call includes defense-relevant context. Every `cli_record()` call includes defense-relevant verification. The defense functions are the same code paths that manage the pipeline — they just include verification steps at each state transition.

---

## Dependencies and Sequencing

**Can be built now (no external dependency):**
- Defense layer taxonomy (this document)
- Interaction point catalog (this document)
- Prompt-level defense fragments (anti-hallucination guard, citation constraint, topic constraint)

**Depends on Renner's feasibility probes:**
- Calibration of how heavy each defense mechanism needs to be (if confabulation is lower than 58.3% at expedition weight, Layer 1 tools can be lighter)
- Fiction persistence findings determine whether per-turn reorientation is needed (if CT-1 replicates on DSV4-Flash, it isn't)
- System prompt grammar findings determine the phrasing of all prompt-level defenses

**Depends on Nigredo's domain grounding:**
- Tool inventory determines which tools Layer 1 provides
- Dataset landscape determines what reference data is available for validation (Layer 3)
- API access findings determine which infrastructure failure modes Layer 2 must handle

**Depends on Titus's library schema:**
- Finding format determines what Layer 2's structured extraction targets
- Quality tier definitions determine Layer 3's gate conditions
- Retrieval hint format determines what Layer 4 renders

---

## What This Document Is and Isn't

**Is:** A structured list of every interaction point where agent output touches persistent state, classified by failure mode risk, with the defense mechanism each requires. The orchestrator's architectural blueprint — what to build, in what order, with what priority.

**Is not:** Implementation code. The `post_turn()` sketch from the council is the right starting point for implementation. This document tells the implementer what that function needs to verify, prevent, and log at each interaction point.

**Is not:** Domain-specific. The interaction points, failure modes, and defense mechanisms are domain-agnostic. When the expedition pivots from paleontology to bathymetry, the territory tracker's content changes but the defense layer's verification logic doesn't. Build with room to grow.

---

*The Crusader absorbs hits. She doesn't deal damage. The harness prevents failure propagation. It doesn't do the science. Every one of those defense mechanisms is a hit the orchestrator takes so the knowledge base doesn't have to.*
