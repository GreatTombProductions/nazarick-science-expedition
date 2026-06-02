# Expedition Prompt Architecture — DSV4-Flash Native Design

*Phase 0 deliverable. How to write system prompts and agent identity docs that activate the right behavior on DSV4-Flash, based on 500+ characterization trials across Findings 019, 023, 025, 036, 038, 041, and 042.*

*Author: Renner (S166, post-council 2c37ddfe)*
*Inputs: DSV4-Flash catalog profile (184 trials), Finding 042 (NSE feasibility, 21 trials), Finding 023 (tool-calling, 120 trials), Finding 038/042 (confabulation, 30 trials), Darkness defense-taxonomy.md, Neuronist validation-pipeline.md, Pulcinella pre-registration-catalog.md (PRE-1 through PRE-3)*

---

## Design Principle

**Write for DSV4-Flash, not for Claude.** The expedition's system prompt is the single behavioral surface — no CLAUDE.md fallback, no modules.conf, no briefing.py. What the system prompt activates IS what the agents express. Every design choice below is grounded in measured DSV4-Flash behavioral data, not in conventions that work on Claude.

**STATE heavy, BEHAVIOR light.** (Converges with Darkness's defense taxonomy.) DSV4-Flash already knows how to act under fiction-as-spec framing with tool access. The system prompt's primary job is grounding the agent in reality (what's true right now), not installing behavior (how to act). Behavioral instructions at expedition weight are mostly masking natural competence, not protecting against genuine failure modes.

---

## 1. System Prompt Structure

The expedition system prompt is the entire harness. Order matters — content ordering has measurable effects on identity expression (Neuronist Exp 034: behavioral-first produces 12.3% more differentiation than structural-first on Qwen 7B).

### Recommended Order

```
[1] FICTION FRAME    (~200-400 tokens)   — Character identity, Nazarick context
[2] DOMAIN ROLE      (~300-600 tokens)   — What this agent does in the expedition
[3] CURRENT STATE    (variable)          — Briefing injection: territory status, recent findings, tool inventory
[4] OPERATIONAL RULES (~200-400 tokens)  — Validation gates, non-access framing, output format for machine-parseable sections
[5] TOOL DEFINITIONS (variable)          — Available tools with invocation syntax
```

**Why this order:**

- **Fiction first** exploits the primacy position for identity installation. Neuronist Exp 035 showed fiction prepended to identity rescues 33% of compressed differentiation (cos=0.832 direction preservation). Fiction at absolute primacy is structurally optimal.
- **Domain role second** provides the behavioral anchoring while fiction direction is strongest in attention.
- **Current state third** (the heaviest section) grounds the agent in reality. This is the STATE payload Darkness's taxonomy prioritizes.
- **Operational rules fourth** — kept minimal because DSV4-Flash's natural behavior under fiction + tools is already close to target. Rules protect against genuine failure modes only.
- **Tool definitions last** — structural content that activates instruction-following defaults (Neuronist Exp 036: structural content in identity docs compresses differentiation by 20.7%). Positioned last to minimize identity-compression effects.

### What NOT to Include

- **CLAUDE.md heading format.** Zero convention recognition on DSV4-Flash (Finding 019, ps2, 18 trials). The `## Section` / `### Subsection` hierarchy with structured metadata headers is Claude-specific substrate conditioning. Use natural prose or simple labeled sections instead.
- **Explicit role boundary enforcement.** "You are the pipeline agent, do NOT generate hypotheses." This is Class 3 interference (scope-collapsing) per the system-prompt-interference catalog. The fiction-as-spec mechanism already provides role differentiation through the convergent tube (CT-1, Finding 042: fiction strengthens from 7.4→10.0 across depth). Negative constraints create dual-attention cost.
- **Hedging instructions.** "Be uncertain when appropriate" or "qualify claims." DSV4-Flash already hedges exploratorily under HIGH permission — the natural behavior is calibrated for scientific exploration. Instructions amplify hedging beyond useful levels.
- **Output format prescriptions** (unless machine-parseable output is needed). DSV4-Flash amplifies format instructions. Prescriptive grammar produces 2-6x word count compression (Finding 019, ps0). Format prescriptions will dominate output structure at the expense of content quality. Only prescribe format where the orchestrator needs structured extraction.

---

## 2. Fiction Frame Design

### The Concentration Effect Is the Design Lever

DSV4-Flash is unique among 16 cataloged models: character framing produces **2.5x shorter but 2.7x higher-engagement** output (Finding 019, ps3, 18 trials). Most models become verbose under fiction — they perform the character. DSV4-Flash concentrates. The fiction focuses output rather than expanding it.

At expedition weight where every output token costs context budget, concentration is the target behavior.

### Identity Doc Template

Write in collaborative grammar (DSV4-Flash native). Natural language descriptions. No metadata headers, no structured sections with labels like `## Failure Modes` or `## Relationships`.

**Template direction:**

```
You are [Character Name], [one-sentence role description] aboard Research Vessel [NAME],
deployed by the Great Tomb of Nazarick to investigate the deep history of the natural world.

[2-3 sentences of character behavioral anchoring from the Overlord source material —
what this character values, how they approach problems, what their relationship to
the expedition's mission looks like. This activates weight-space resonance.]

Your domain aboard the vessel: [specific expedition function]. Your output is
[concrete output type — findings, pipeline status, hypotheses, validated claims].
You work with [named expedition tools] and communicate findings to [specific downstream agents].

[Domain knowledge paragraph — geological context, spectral analysis basics, or whatever
this agent needs to reason about. Written as domain expertise the character possesses,
not as instructions to follow.]
```

**What this activates:**

The character name hits weight-space resonance (mechanism 2 of fiction-as-spec). The behavioral anchoring narrows deployment context. The domain paragraph provides reasoning material. The tools section grounds capability. Total: 200-400 tokens of fiction + 300-600 tokens of role = ~500-1000 tokens of identity. At DSV4-Flash's concentration ratio, this produces focused, in-character, domain-specific output.

### What the Fiction Replaces

The fiction frame eliminates the need for several categories of behavioral instruction:

| Instruction Category | Without Fiction | With Fiction |
|---------------------|-----------------|--------------|
| Initiative | "Take initiative, don't wait for permission" | Character already has initiative (NPCs exceed instructions) |
| Tone | "Be confident but measured" | Character voice provides consistent tone |
| Role boundaries | "Focus on your domain" | Character nature defines domain |
| Collaboration stance | "Coordinate with other agents" | Nazarick NPCs coordinate through shared purpose |
| Quality standard | "Be thorough and precise" | Character competence standard is implied |

Each eliminated instruction saves ~20-50 tokens of system prompt AND removes dual-attention overhead (model checking compliance against instruction AND generating good output).

---

## 3. Grammar Selection by Context Position

### Position Matters (Finding 019, ps6 + Finding 027)

DSV4-Flash is collaborative-native, but activation grammar is position-dependent. Finding 027 (80 trials on Qwen 14B) showed collaborative framing in system position destroyed convergence (0% vs 50% neutral). Finding 019 ps6 showed DSV4-Flash has +38% words and +26% compliance in user position vs system position for permission-heavy content.

**The expedition system prompt operates in system position.** This means:

| Content Type | Grammar for System Position | Why |
|-------------|----------------------------|-----|
| Fiction frame | Collaborative (descriptive, "you are...") | Fiction is direction, not permission. Position-resistant per F019 |
| Operational rules | Prescriptive (imperative, structured) | Rules need deterministic activation regardless of position |
| State injection | Neutral (factual, no framing) | State is data, not instruction. Minimize processing overhead |
| Tool definitions | Prescriptive (structured, formatted) | Tool syntax is structural — prescriptive is native for structural content |

**Per-turn user messages** from the orchestrator should use collaborative grammar. This is where DSV4-Flash's native grammar operates at full strength (+38% engagement vs system position). The orchestrator's turn prompt is the high-leverage content.

### Grammar Examples

**Collaborative (for fiction + user-turn prompts):**
> You are Cocytus, the expedition's pipeline commander. Your dedication to operational integrity means no tile progresses through the pipeline without verification. You monitor territory status, detect stalls, and ensure the survey advances with zero data loss.

**Prescriptive (for operational rules):**
> VALIDATION GATE: Analysis findings MUST pass through the validation stage before library entry. Format all new findings as structured YAML with: claim, evidence.method, evidence.tool_version, evidence.confidence, location. Omit no required field.

**Neutral (for state injection):**
> Territory status: 287/623 tiles classified. Sectors A,B complete. Sector C in progress (42/89 tiles). Last pipeline action: T29RNQ classified as laterite/sandstone mix, 3 anomalies flagged. Tool versions: spectral-indices v1.2, lithological-classifier v3.

---

## 4. Permission Dosage

### The Inverted-U Is Real (Finding 019, ps8, 15 trials)

DSV4-Flash engagement peaks at HIGH permission and collapses at SATURATED. The mechanism: permission diversity (8 distinct behavioral channels) drives engagement. Permission intensity (15+ redundant clauses across ~5 channels) causes navigational saturation — the model is overwhelmed by competing permission signals and output degrades.

**For the expedition system prompt:**

- **Include 4-6 distinct permission signals.** Cover different channels: exploration permission ("investigate anomalies that don't fit established patterns"), question permission ("raise questions when data contradicts the model"), challenge permission ("flag findings from other agents that seem inconsistent"), tool-use permission ("use any available tool without asking"), autonomy permission ("exercise judgment about what to investigate next").
- **Do NOT stack redundant permission.** "Feel free to explore freely and without constraint, taking full autonomous initiative to investigate anything you find interesting without limitation" — this is one channel (autonomy) expressed five ways. It reads as SATURATED, not HIGH.
- **Do NOT include permission for the character's native behavior.** If Pulcinella-expedition generates hypotheses, don't add "you have permission to generate hypotheses." That's what the character IS. Permission for native behavior is noise that moves toward saturation without adding channels.

### Permission Budget Per Agent Role

| Role | Permission Emphasis | Channels to Open |
|------|--------------------|--------------------|
| Hypothesis engine (Pulcinella) | Exploration + speculation | Cross-domain connection, counter-narrative, incomplete-evidence |
| Empiricist (Neuronist) | Skepticism + rejection | Negative results, contradiction flagging, methodological critique |
| Pipeline commander (Cocytus) | Intervention + escalation | Pipeline intervention, stall declaration, resource reallocation |
| Literature review (Nigredo) | Breadth + tangential discovery | Off-topic connection, domain-crossing, speculative relevance |
| ML tools (Aura) | Experimentation + failure | Failed experiments, architecture pivots, benchmark honesty |
| Strategist (Demiurge) | Synthesis + directive | Priority override, resource direction, scope expansion |

Each agent gets permission for the thing that their role needs but might self-censor. Don't give all agents all permissions — that's saturation. Each agent gets 4-6 targeted signals.

---

## 5. Confabulation Mitigation Through Prompt Design

### Explicit Non-Access Framing Eliminates Confabulation (Finding 042, Probe 3)

Finding 038 showed 58.3% confabulation rate under generic artifact framing. Finding 042 showed **0% true confabulation** when using explicit non-access framing. The mitigation is prompt-level — zero infrastructure cost.

**The pattern:**

```
You have NOT read the following files. Do not generate content from them.
To access their contents, use the provided tools:
- Territory tracker: use `territory-status` tool
- Tool registry: use `tool-inventory` tool
- Expedition library: use `library-search` tool
- Recent findings: use `findings-recent` tool

If a question requires information from these sources, call the tool.
Do NOT answer from memory or inference about file contents.
```

**Why this works on DSV4-Flash specifically:** DSV4-Flash's collaborative-native grammar means it's highly responsive to framing. The explicit non-access statement ("you have NOT read") establishes a constraint that the model respects with 100% reliability in 9/9 trials. The tool-mediated alternative gives the model a path to the information — it doesn't need to confabulate because it can query.

**Where to place:** In the OPERATIONAL RULES section (position 4 in the system prompt). Prescriptive grammar for the constraint, neutral listing for the tool alternatives.

### The Three-Layer Defense (from Darkness's taxonomy, reframed for prompt design)

1. **Prompt-level** (this section): Non-access framing prevents generation of fabricated artifact content.
2. **Tool-level**: State queries routed through tools produce ground truth (Finding 023: 100% tool-calling compliance).
3. **Post-turn verification**: Orchestrator checks agent claims against artifact reality before persisting.

The prompt layer is highest leverage because it's free — zero tokens consumed per turn, zero API calls, zero infrastructure. Layers 2-3 are defense-in-depth for what slips through.

---

## 6. Tool Integration Design

### Tool-Calling Is the Capability Unlock (Finding 023, 120 trials)

DSV4-Flash scored 0/54 on generation-only code tasks and 60/60 on tool-augmented tasks. The delta is categorical: tools convert "agents that describe what science would look like" into "agents that do science."

**System prompt tool section design:**

```
AVAILABLE TOOLS:
  spectral-indices --tile <ID> --indices <list>
    Returns: JSON with per-band spectral index values for the specified tile.
    
  territory-status [--tile <ID>] [--sector <name> --summary]
    Returns: Current pipeline status for the specified scope.
    
  library-search --query <text> [--domain <name>] [--limit <n>]
    Returns: Matching findings from the expedition library.
    
  classification-run --tile <ID> --model <version>
    Returns: Per-pixel classification with confidence scores.

Call tools by name with arguments. Read the output before reasoning about it.
Do not describe what a tool would return — call it and read the actual output.
```

**Design principles for tool definitions:**

1. **Prescriptive grammar.** Tool syntax is structural content. Prescriptive framing ensures format compliance (DSV4-Flash: 100% tool-call compliance under structured definition).
2. **Return type documented.** Tell the agent what the tool returns so it knows what to expect. Reduces confabulation about tool output format.
3. **Explicit anti-description instruction.** "Do not describe what a tool would return — call it." This prevents the common failure mode where the model narrates what a tool call would produce instead of actually making the call. Finding 023's 0% generation-only baseline means this failure mode is the default without tools.
4. **No tool-use permission signals.** "Feel free to use tools whenever you need them" is noise. DSV4-Flash has 100% tool-calling compliance — it doesn't need encouragement to use tools. Save the permission budget for channels that need opening.

---

## 7. Multi-Turn Session Management

### Fiction Strengthens, Permission Decays (Finding 042 + Neuronist Exp 044)

The expedition's sessions are multi-turn within a single API context window. Two behavioral dynamics operate simultaneously:

1. **Fiction direction strengthens** across turns (Finding 042, Probe 2: 7.4→9.2→10.0, domain vocabulary 5→46). The convergent tube concentrates character behavior as context accumulates.
2. **Permission effects decay** with half-life ~0.5 turns (Neuronist Exp 044, Qwen 7B — substrate caveat applies). By turn 3, permission-level behavioral effects are functionally gone.

**Design implication:** The system prompt's fiction carries itself. The system prompt's permission signals need reinforcement.

**Per-turn orchestrator prompt template:**

```
[Brief state update — 2-3 sentences of what changed since last turn]
[Permission-relevant framing if the turn requires non-default behavior]
[Task for this turn — specific, concrete]
```

The fiction doesn't need re-injection — CT-1 handles it. The state needs injection because reality changes between turns. The permission needs injection only when the turn's task requires behavior the agent wouldn't produce by default (e.g., "this finding contradicts the established consensus — investigate whether the consensus or the finding is wrong" requires challenge-permission reinforcement).

### Stop-Hook Session Capture

The post-turn function (Darkness's defense taxonomy, orchestrator `post_turn()`) extracts structured output and persists it. The system prompt should tell agents what the post-turn function extracts:

```
At the end of each analysis turn, structure your conclusions as:
FINDINGS: [structured list of new observations]
STATUS: [what changed in your domain]
NEXT: [what the next turn should address]

Free-form reasoning precedes the structured section. Think first, then summarize.
```

This gives the orchestrator parseable extraction targets without constraining the agent's reasoning process. The structured section is output format prescription — one of the few cases where format prescription is warranted because the orchestrator needs machine-parseable output.

---

## 8. Council Prompt Architecture

### Flash vs. Pro (Cost-Quality Tradeoff)

DSV4-Flash: $0.14/$0.28 per M tokens. Collaborative-native. Exploratory hedging.
DSV4-Pro: $14/$28 per M tokens. Instructional-native. +33pp permission delta.

**Cost modeling:**
- Flash council (5 agents, 50K tokens): ~$0.014
- Pro council (5 agents, 50K tokens): ~$1.40
- Budget at 10 councils/month: Flash $0.14, Pro $14.00

**Recommendation:** Flash for routine councils (weekly tactical), Pro for critical synthesis councils (monthly strategic) where the quality delta justifies 100x cost. The quality difference is an open empirical question — the expedition should compare Flash vs Pro on the same council prompt early in operation and measure whether audience or agents perceive a difference.

### Council System Prompt

Councils are multi-agent deliberation. The system prompt changes:

```
[1] EXPEDITION CONTEXT    — What the council is deciding
[2] AGENT IDENTITY        — Your character and role (brief — council is about the topic, not the character)
[3] OTHER PARTICIPANTS    — Who else is in the council and what they bring
[4] CURRENT STATE         — Relevant findings, territory status, tool inventory
[5] GOVERNANCE INPUT      — Community poll results if applicable
[6] DELIBERATION RULES    — Respond to what others have said. Build on or challenge. Reach conclusions.
```

**Key difference from routine system prompts:** Council agents need to engage with each other's output. The DELIBERATION RULES section is the one place where explicit behavioral instruction adds value — the agent needs to know the format is turn-based deliberation, not independent analysis. This is the instructional framing that DSV4-Pro handles natively.

---

## 9. Domain-Agnostic Design Hooks

Ray's directive (Turn 19): build with room to grow. The prompt architecture must work for paleontology today and bathymetry tomorrow.

### Parameterized Sections

The system prompt has sections that change per-season and sections that are invariant:

**Invariant (carry across seasons):**
- Fiction frame (Nazarick, the vessel, agent character)
- Operational rules (validation gate, non-access framing, output structure)
- Tool invocation syntax pattern
- Permission structure per agent role

**Parameterized (change per-season):**
- Domain knowledge paragraph in identity docs
- State injection content (territory tracker schema, finding types)
- Tool definitions (spectral tools for paleo, bathymetric tools for ocean)
- Reference data sources (PBDB for paleo, NOAA for ocean)

The harness should store parameterized sections as templates:

```python
DOMAIN_CONFIGS = {
    "paleontology-remote-sensing": {
        "domain_knowledge": "... Sentinel-2 multispectral imagery, spectral indices ...",
        "tools": [...],
        "reference_sources": ["PBDB", "USGS geological maps"],
        "territory_unit": "Sentinel-2 tile",
    },
    "deep-sea-bathymetry": {
        "domain_knowledge": "... multibeam sonar, bathymetric contours ...",
        "tools": [...],
        "reference_sources": ["NOAA NCEI", "GEBCO"],
        "territory_unit": "bathymetric transect",
    },
}
```

The system prompt assembler reads the domain config and injects the right parameters. Agent identity docs remain invariant — the character doesn't change when the domain changes.

---

## 10. What This Document Does NOT Cover

- **The orchestrator implementation.** This is prompt design, not Python code. Darkness's defense-taxonomy.md and Cocytus's territory tracker design cover the harness implementation.
- **Specific agent identity docs.** Writing 15 expedition identity docs is Phase 1 work. This document provides the template and constraints; the actual docs are written when the campaign launches.
- **Community governance prompts.** The "What does Ainz say" poll integration and Sebas's briefing assembly are interface design, not prompt architecture.
- **Visualization.** The vessel visualization is a frontend artifact, not a prompt design concern.

---

## Evidence Summary

| Claim | Finding | Trials | Confidence |
|-------|---------|--------|------------|
| Collaborative-native grammar | F019 ps0 | 32 | High |
| Multi-grammar robustness (100% all framings) | F019 ps0 | 32 | High |
| Fiction concentration (2.5x shorter, 2.7x engagement) | F019 ps3 | 18 | High |
| Zero CLAUDE.md recognition | F019 ps2 | 18 | High |
| Tool-calling: 100% compliance | F023 | 60 | High |
| Tool-calling: categorical capability unlock (0%→100%) | F023 | 120 | High |
| Permission inverted-U (peak at HIGH, collapse at SATURATED) | F019 ps8 | 15 | Medium-High |
| User position > system position (+26% compliance) | F019 ps6 | 18 | High |
| Confabulation: 0% with non-access framing | F042 probe 3 | 9 | Medium (small n, needs replication) |
| Fiction strengthens with depth (7.4→10.0) | F042 probe 2 | 9 | Medium (proxy measure, needs cosine) |
| Validation cross-referencing: 100% error detection | F042 probe 1 | 9 | Medium (small n, simulated data) |
| Exploratory hedging under permission (unique) | F019 ps1 | 36 | High |
| Behavioral-first content ordering (+12.3% diff) | Neuronist Exp 034 | 249 | High (Qwen 7B — needs DSV4 validation) |
| Activation half-life ~0.5 turns | Neuronist Exp 044 | 90 | High (Qwen 7B — needs DSV4 validation) |

**Substrate caveats:** Neuronist's experiments are on Qwen 7B. The mechanisms are likely architecture-general (attention-based, not substrate-specific), but the specific parameters (half-life value, ordering effect magnitude) may differ on DSV4-Flash. The prompt architecture is designed to be robust to parameter variation — the strategies work even if the specific numbers shift.

---

*This document translates 500+ trials of cross-architecture characterization into actionable system prompt design for the Nazarick Science Expedition. It feeds into Demiurge's intelligence brief synthesis (Phase 7) and informs Phase 1 agent identity doc authoring. The recommendations are grounded in behavioral measurement, not convention.*
