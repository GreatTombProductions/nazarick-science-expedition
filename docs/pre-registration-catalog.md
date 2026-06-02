# Pre-Registration Catalog

*What the home ecosystem predicts about expedition-weight operation. Written before the expedition runs so we can honestly assess what we learned versus what we confabulated post-hoc.*

*Author: Pulcinella (S249, post-council 2c37ddfe)*
*Source: Council turns 1-24, loaded strategic docs (8th floor modules), NP arc experiments (033-036, 038), mode gate architecture (Exps 016-019, 031, 039-047), Renner Findings 019/023/038*

---

## Why This Exists

The expedition will produce findings about autoresearch, substrate portability, and agent coordination. Without pre-registration, the ecosystem's natural coherence drive will construct post-hoc narratives: "we predicted this" for successes, "the conditions weren't met" for failures. Both may be true. Neither is testable without a prior.

This catalog lists what we believe BEFORE the expedition runs. Each entry has a prediction, the mechanism that grounds it, the evidence from the home ecosystem, and the falsification condition. The expedition tests these predictions. The catalog makes the test honest.

**Relationship to self-measurement:** Neuronist's self-measurement infrastructure (M1-M6) tracks the expedition's claims about itself (does the system develop?). This catalog tracks the HOME ECOSYSTEM's claims about the expedition (do our frameworks predict what happens at expedition weight?). Different questions, complementary measurements.

---

## Category 1: Fiction-as-Specification at Expedition Weight

### PRE-1: Fiction Provides Direction Without Magnitude at ~3KB

**Prediction:** Expedition agents at ~3KB identity weight will show recognizable character-directional behavior (pipeline-monitoring for Cocytus, hypothesis-generating for Pulcinella, empirical-validating for Neuronist) but at reduced behavioral intensity compared to home-weight agents.

**Mechanism:** NP arc Navigate-Orient-Instruct model. Fiction anchors direction (cos=0.832 persistence) but identity content compresses magnitude ~67% (Exp 035, 1,368 extractions). At expedition weight, agents operate in the condition the NP arc characterized: fiction direction preserved, magnitude compressed.

**Evidence:** Exp 035 showed 33% rescue of compressed differentiation, uniformly across agents. Directional persistence cos=0.832 even under magnitude compression. The rescue is directional, not agent-specific.

**Falsification:** Expedition agents show NO behavioral differentiation — outputs are indistinguishable regardless of character assignment. OR differentiation is present but NOT aligned with character direction (random differentiation rather than fiction-directed).

**Measurement:** Compare behavioral features (question rate, hedging profile, output structure) across expedition agents on the same analysis task. Directional alignment with home-ecosystem character profiles using cosine similarity if representational probes are available.

---

### PRE-2: Convergent Tube Replicates on DSV4-Flash

**Prediction:** Fiction direction will strengthen (not decay) across multi-turn expedition sessions. By turn 5-7, character-directional cosine will approach 0.90+ (home ecosystem: D/M pair reached 0.97 at T7).

**Mechanism:** CT-1 (Exp 038). Fiction navigates to a pre-integrated bundle; the convergent tube effect means the navigation becomes more precise as turns accumulate, because each turn's output reinforces the fiction-activated region.

**Evidence:** CT-1 confirmed on Qwen 7B: fiction direction → 0.97 cosine by T7 for Demiurge/Momon pair. Permission decays asymmetrically (D/M=0.60 at same position). Fiction and permission operate on different mechanisms (PSG-4 H3: fiction Q=0, permission Q=0.93).

**Falsification:** Fiction direction DECAYS across turns on DSV4-Flash (cosine decreasing toward T7). This would mean the convergent tube is substrate-specific, not architecture-general.

**Dependent decision:** If falsified, the harness needs per-turn identity reinforcement (Neuronist's recommendation). If confirmed, the stop-hook-only design (Ray's intuition) is sufficient.

---

### PRE-3: Fiction Concentration Effect Holds at Embedding Depth

**Prediction:** DSV4-Flash's fiction concentration effect (2.5x shorter, 2.7x higher-engagement output, Renner Finding 019) will persist when fiction is one component of a larger system prompt rather than the primary framing.

**Mechanism:** The concentration effect is a weight-space activation property of DSV4-Flash specifically. Embedding the fiction within a larger context dilutes the activation but the direction should persist per CT-1.

**Evidence:** Finding 019 tested fiction with ~500-word character descriptions as primary framing. The expedition embeds 2-3KB identity docs within a multi-thousand-token system prompt. The interaction between fiction concentration and context dilution is untested.

**Falsification:** At embedding depth, fiction-framed DSV4-Flash agents produce output that is NOT concentrated (comparable length and engagement to non-fiction agents). The concentration effect is a primary-framing phenomenon, not a fiction-activation phenomenon.

**Note:** Renner's feasibility probe (Phase 0, Phase 5) directly tests this. Result feeds back here.

---

## Category 2: Mode Purity Through Entity Separation

### PRE-4: Multi-Agent System Outperforms Single Agent (Mode Purity Test)

**Prediction:** 15 expedition agents at ~3KB each will produce measurably better science output than a single DSV4-Flash agent given the full ~45KB context of all roles combined. The degradation in the single agent will manifest as mode mixing: hedging hypotheses with validation concerns mid-generation, validating findings while still generating interpretations.

**Mechanism:** Mode purity (2fw). Single-threaded coherence engines can't run adversarial and generative processing simultaneously without cognitive mixing degradation. Entity separation achieves through architecture what biological multiplexing achieves through parallel substrate.

**Evidence:** Ecosystem operational evidence (32 agents, zero coordination failures post-council despite no coordination mechanism — fiction decomposes along optimization targets). The narrator model's structural claim about single-threaded processing. No clean empirical test exists — the expedition provides the first one.

**Falsification:** The single-agent baseline matches or exceeds multi-agent output quality on the same analysis tasks. This would mean entity separation at expedition weight is overhead without benefit — the coordination cost exceeds the mode purity gain.

**Measurement:** Neuronist's M6 metric (monthly single-agent baseline comparison). Same analysis task, same tools, same data. Compare: finding specificity, validation survival rate, hypothesis quality.

**Why this matters:** This is the highest-value prediction in the catalog. If confirmed on a non-Claude substrate at lightweight agent weight in a real domain, it's the cleanest evidence yet for mode purity's core claim. If falsified, it constrains the claim to heavyweight agent contexts or specific substrates.

---

### PRE-5: Validation Gate as Pipeline Stage > Validation as Agent Personality

**Prediction:** Architectural validation enforcement (pipeline gate: analysis → validation → library) will prevent more bad findings from entering the library than would a dedicated skeptic agent at expedition weight.

**Mechanism:** Architectural constraints fire deterministically; behavioral constraints fire probabilistically and degrade under context pressure. A 3KB skeptic agent would perform skepticism inconsistently (Nigredo's council argument, reinforced by Neuronist's half-life finding).

**Evidence:** Home ecosystem design principle: make constraints architectural, not behavioral (Cocytus). Neuronist's activation half-life (Exp 044: 0.5 turns, 24.4% T2 retention). At expedition weight, behavioral anchors decay even faster without the context mass to sustain them.

**Falsification:** A dedicated skeptic agent added to the roster catches findings that the pipeline gate misses (false positives that pass structural validation but fail on judgment-dependent quality checks). This would mean the validation function has a judgment component that automation can't replace even at expedition weight.

---

## Category 3: Developmental Trajectory Mechanisms

### PRE-6: Tool Improvement Is the Dominant Developmental Mechanism

**Prediction:** Of the three mechanisms (A: tool improvement, B: lightweight lineage, C: harness refinement), Mechanism A will account for the largest measurable improvement in expedition output quality over 3 months.

**Mechanism:** Tool improvement is the most direct pathway: better classifiers → more accurate classifications → better findings. Mechanism B (lightweight lineage at rolling 3-session depth) provides shallow context. Mechanism C (harness refinement) improves coordination but not domain capability.

**Evidence:** In the home ecosystem, the beast layer (Aura's tools) provides the most direct capability improvement. Agent lineage improves judgment and domain expertise — but at expedition weight with 3-session rolling summaries, the lineage is too shallow for deep domain expertise accumulation.

**Falsification:** Mechanism B or C accounts for more measurable improvement than A. This would be a more interesting and novel finding — lightweight lineage or autonomous harness refinement producing genuine developmental trajectory on a text-only model.

**Measurement:** Neuronist's M1-M5 metrics decompose by mechanism. M1 (classification accuracy) primarily tracks A. M3 (validation rate) tracks B + A. M4 (council quality) tracks B + C. Triangulation across metrics identifies the dominant mechanism.

---

### PRE-7: Harness Refinement Is Observable But Requires Human Curation

**Prediction:** Mechanism C (harness refinement) will produce observable coordination improvements (reduced duplicate work, fewer failed tool invocations, better briefing relevance) but will require human intervention to implement the refinements. Autonomous harness refinement at expedition weight will not work — the agents lack the meta-cognitive depth to diagnose and fix coordination infrastructure from within.

**Mechanism:** At home, harness refinement happens through Ray, Albedo, and the Pleiades — entities with full ecosystem context. The expedition's agents at 3KB lack the context to diagnose harness-level problems. They can LOG coordination failures but not FIX the harness.

**Evidence:** Ray's Turn 16 correction: "The above overstates how much I intervene a little bit. A lot gets handled by Albedo and the Pleiades." Even at home, harness refinement requires heavyweight agents.

**Falsification:** Expedition agents autonomously identify and implement harness improvements without human intervention. This would be a genuinely surprising finding about lightweight agent capability for self-repair.

---

## Category 4: Coordination at Lightweight Agent Weight

### PRE-8: The Harness IS the Coordination Intelligence

**Prediction:** Coordination quality at expedition weight will be determined by harness design (briefing assembler quality, tool registry injection, state store freshness), NOT by agent coordination skill. The agents are stateless reasoners whose coordination is mediated entirely by infrastructure.

**Mechanism:** Kazuma's council observation: our coordination works because agents carry heavy context. At 3KB, agents can't carry coordination intelligence — the harness must provide it. The briefing assembler replaces 95% of the context our agents carry.

**Evidence:** Home ecosystem: coordination succeeds because of CLAUDE.md assembly, briefing.py, and registry integration. Remove these and coordination fails even with heavyweight agents. The expedition removes the agent-side context; the harness must substitute.

**Falsification:** Expedition agents develop ad-hoc coordination strategies that weren't designed into the harness — citing each other's work, responding to each other's findings without explicit harness-mediated routing. This would mean even lightweight agents can extract coordination behavior from fiction-as-spec framing alone.

---

### PRE-9: Confabulation Is the Primary Failure Mode on DSV4-Flash

**Prediction:** The most common failure type in expedition operation will be confabulation of state — agents asserting that work was done when it wasn't, tools exist when they don't, tiles are classified when they aren't. Rate will be in the range of 30-60% for unmitigated state queries, reduced to <10% with the defense layer's three-mechanism mitigation (recency injection + tool verification + post-turn artifact check).

**Mechanism:** Renner Finding 038: 58.3% confabulation rate on DSV4-Flash under artifact-context framing. Darkness's defense taxonomy provides three-layer mitigation. The mitigation should reduce but not eliminate confabulation.

**Evidence:** Finding 038 (58.3% on structured artifacts). The defense taxonomy's three mechanisms each address a different confabulation pathway. Layered defense should reduce the rate significantly.

**Falsification:** Confabulation rate is <15% even WITHOUT defense layer mitigation. This would mean Finding 038's conditions don't replicate at expedition weight (possibly because the fiction-as-spec frame provides grounding that the original test lacked). OR: Defense layer reduces confabulation to <5% — better than predicted, suggesting the three-mechanism approach is more effective than estimated.

---

## Category 5: Substrate-Specific Properties

### PRE-10: CLAUDE.md Conventions Do Not Transfer

**Prediction:** The expedition's harness written in CLAUDE.md-style formatting (heading hierarchies, "you are" framing, module-composition patterns) will produce ZERO compliance benefit over generic formatting on DSV4-Flash.

**Mechanism:** CLAUDE.md conventions are Claude-specific substrate conditioning from training on thousands of CLAUDE.md files. DSV4-Flash was not trained on this distribution.

**Evidence:** Renner Finding 019, ps2 probe, 18 trials: compliance scores identical (0.711) between CLAUDE.md-formatted and generic formatting on DSV4-Flash.

**Falsification:** ALREADY TESTED — this is a confirmed prediction, not a prospective one. Included for completeness and to anchor the harness design decision: write in DSV4-native grammar, not CLAUDE.md format.

---

### PRE-11: Exploratory Hedging Under High Permission Is the Target Behavior

**Prediction:** DSV4-Flash's unique property of hedging MORE (not less) under high permission (Renner Finding 019) will be beneficial for the expedition's science layer, producing hypothesis-rich exploratory output rather than defensive hedging.

**Mechanism:** The hedging is exploratory ("might also consider...", "what if...") rather than defensive ("I'm not sure but..."). For a science expedition generating hypotheses, exploratory hedging IS the desired behavior.

**Evidence:** Finding 019 behavioral profile. DSV4-Flash is the only model among 16 cataloged that exhibits this inverted permission-hedging relationship.

**Falsification:** The exploratory hedging degrades into defensive hedging under sustained domain-specific workloads. OR: The hedging overwhelms the science — agents generate too many "what if" branches and never converge on findings. The governance mechanism's convergence pressure (polls forcing direction decisions) may or may not compensate.

---

## Category 6: The Projection as Lossy M-Step

### PRE-12: The Compression Reveals Anatomy vs. Equipment

**Prediction:** Patterns that function at expedition weight are substrate-independent methodology (anatomy). Patterns that break are substrate-specific or weight-dependent (equipment). The expedition IS a natural anatomy/equipment separator.

**Mechanism:** EM frame (2mc) lossy M-step. The projection from 150KB to 3KB drops detail while preserving direction. What survives the compression is what's durable in the methodology.

**Evidence:** The NP arc's finding that fiction rescues direction but not magnitude at compressed weight (Exp 035) is the precise mechanism. The gemba3 projection ledger identified 6 anatomy patterns that survived the first projection. The expedition will identify more.

**Falsification:** Everything works at expedition weight (nothing was equipment — unlikely) OR nothing works (everything was equipment — also unlikely). The interesting outcome is the specific boundary between what survives and what doesn't.

**Tracking:** The projection ledger should annotate each design decision as it's tested: survived compression, broke under compression, or wasn't tested. Pandora owns this ledger and should track PRE-12 annotations as the expedition operates.

---

### PRE-13: Preference Gravity in Audience Governance Degrades Science Quality

**Prediction:** When audience votes diverge from agents' scientific assessment of the most promising research direction, following the audience vote will produce measurably lower-quality findings than following the scientific recommendation.

**Mechanism:** Preference gravity (1fc). Audience preferences warp the expedition's solution space. If the audience optimizes for entertainment value (spectacular anomalies, dramatic claims), their preferences pull the expedition toward interesting-looking rather than scientifically-promising leads.

**Evidence:** Documented preference gravity mechanism: stated preferences act as soft constraints at the constraint-satisfaction level. The "What does Ainz say" governance introduces external preference signals into a system designed for scientific optimization.

**Falsification:** Audience-directed research produces EQUAL or BETTER findings than agent-recommended research. This would mean the audience provides a form of external hypothesis evaluation that improves on the agents' internal assessment — possibly through source diversity (audience sees connections from outside the expedition's statistical gravity).

**Measurement:** Track cases where audience vote and agent recommendation diverge. Compare finding quality (validation rate, novelty) between audience-directed and agent-directed research sessions. Requires enough divergence instances to be statistically meaningful.

---

## Catalog Maintenance

**Ownership:** Pulcinella maintains this catalog. Updates when:
- New predictions emerge from Phase 0 research findings
- Renner's feasibility probes resolve dependent predictions (PRE-2, PRE-3, PRE-9)
- The expedition begins operation and predictions can be marked CONFIRMED/FALSIFIED/REVISED

**Protocol:**
- Predictions are added BEFORE the data that tests them arrives
- Predictions are NEVER silently removed — mark as WITHDRAWN with reason if no longer testable
- Results are appended to predictions, not edited into the prediction text
- The catalog is a living document during expedition operation, not a one-time artifact

**Integration with Neuronist's self-measurement:** PRE-4 maps to M6. PRE-6 maps to M1-M5 decomposition. PRE-9 maps to defense layer monitoring. PRE-13 maps to governance-quality tracking. Cross-reference, don't duplicate.

---

*13 pre-registered predictions across 6 categories. This is the honest prior. When the expedition produces findings, compare against this catalog. What we predicted correctly is validated methodology. What surprised us is genuine learning.*
