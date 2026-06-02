---
title: "Autoresearch Architecture Teardown"
date: 2026-06-02
author: nigredo
campaign: nse-phase-0-intelligence-brief
phase: autoresearch-teardown
type: architecture-decomposition
---

# Autoresearch Architecture Teardown

**Purpose:** Code-level decomposition of existing autoresearch frameworks. Extract orchestration patterns, state management approaches, evaluation mechanisms, and stealable decisions — not code, decisions. Focus on what the expedition can adopt and where it must innovate.

**Bottom line:** All three frameworks converge on filesystem-as-state and LLM-as-evaluator. None implement knowledge accumulation with staleness detection or dynamic pipeline recomposition — both are things the expedition needs. The highest-value steal is PaperOrchestra's score-delta acceptance policy (principled quality ratchet). Kazuma's prediction was correct: state management between lightweight agent invocations is the most valuable pattern to study.

---

## 1. The AI Scientist (Sakana AI)

**GitHub:** SakanaAI/AI-Scientist (8.9K+ stars, 1.3K+ forks)
**Nature publication:** March 2026 — first fully AI-generated paper to pass peer review at ICLR workshop (score 6.33, above average acceptance).

### Orchestration Pattern

**Fixed linear pipeline.** `launch_scientist.py` calls four functions in strict sequence:

```
generate_ideas() → perform_experiments() → perform_writeup() → perform_review()
```

Optional `perform_improvement()` feeds review back into writeup. Parallelism exists only across ideas (multiprocessing.Queue with GPU-pinned workers, 150s sleep between spawns). No branching, no dynamic routing.

### State Management

**Entirely filesystem-based.** Each idea gets a timestamped directory (`results/{experiment}/{timestamp}_{name}/`), created by `shutil.copytree` from a template. State passes between steps via:

| Artifact | Role |
|----------|------|
| `notes.txt` | Plain text accumulation of per-run results (append-only) |
| `final_info.json` | Structured experiment metrics per run |
| `ideas.json` | Full idea archive with novelty flags |
| LaTeX files + PDF | Compiled paper output |

The Aider `Coder` object is the in-memory state bridge — holds file context and chat history — but is reconstructed fresh for the writeup phase with different `fnames`. No database, no structured inter-step protocol.

### Evaluation Mechanism

Two-layer:

1. **Experiment loop:** Checks `final_info.json` for numeric metrics, feeds back as text for next iteration (max 4 retries, 5 total runs).
2. **NeurIPS-style review:** Generates 5 independent reviews at temperature 0.75, each with 5 self-critique rounds (early "I am done" convergence), then meta-review Area Chair prompt averaging numeric scores. Novelty checking queries Semantic Scholar/OpenAlex with backoff retry.

### What Breaks

- Experiment `subprocess.run` with 7200s timeout + 1500-char stderr cap — silent failures undetected.
- Citation loop runs up to 20 rounds of search-and-integrate — can hallucinate references.
- Review ensemble is hardcoded to GPT-4o regardless of generation model.
- `notes.txt` is append-only — no mechanism to detect contradictions between accumulated entries.

### Stealable Decisions

| Decision | Transfer Quality | Description |
|----------|-----------------|-------------|
| **Idea archive with reflection** | A | Generate ideas iteratively, each seeing all prior ideas, with explicit self-critique and early convergence detection |
| **Ensemble review with meta-aggregation** | A | Multiple independent reviews at high temperature + separate aggregation call |
| **Novelty gate before compute** | A- | Check novelty before committing expensive experiments |

---

## 2. PaperOrchestra (Google Research)

**GitHub:** google-research/PaperOrchestra

### Orchestration Pattern

**Fixed 4-agent pipeline:**

```
OutlineAgent → HybridLiteratureAgent → SectionWritingAgent → ContentRefinementAgent
```

Optional PlottingAgent variant adds a fifth agent. Pipeline has retry logic (max 3 attempts) wrapping the entire sequence. Batch processing uses ProcessPoolExecutor with persistent JSON log for resumability.

### State Management

Agent outputs flow forward through **explicit typed artifacts:**

| Artifact | Type | Role |
|----------|------|------|
| `outline_v1.json` | JSON | Structured outline |
| `template.tex` + `references.bib` | LaTeX | Literature agent output |
| Citation mappings | Structured data | Cross-references |
| `raw_draft_paper.tex` | LaTeX | Section writer output |

The ContentRefinementAgent maintains internal state: `self.current_tex`, `self.current_score`, `self.worklogs` (JSON history). Each refinement iteration produces versioned peer review snapshots (`peer_reviews/review_*.json`), PDF screenshots per version, and structured worklogs.

### Evaluation Mechanism

**Score-delta acceptance policy** — the most sophisticated of the three:

- 7 evaluation axes: Originality, Quality, Clarity, Significance, Soundness, Presentation, Contribution
- **Accept-continue** if Overall score increases
- **Stop-and-revert** if Overall decreases
- If Overall unchanged: compare total_gain vs total_drop across all axes
- Additionally: vision-language model screenshots the PDF and compares against formatting guidelines

Autoraters include `citation_f1.py` (precision/recall on citations), `lit_review_quality.py`, and side-by-side comparison raters.

### What Breaks

- **Write-only pipeline** — no agent can request re-execution of a prior agent. Wrong outline = all downstream wasted.
- 3-retry wrapper retries the *entire* pipeline, not individual steps.
- Formatting loop hardcoded to 1 iteration.
- Gemini-native (model names show `gemini-3.1-pro-preview`) — limited portability.

### Stealable Decisions

| Decision | Transfer Quality | Description |
|----------|-----------------|-------------|
| **Score-delta acceptance with revert** | A+ | Principled quality ratchet — no absolute thresholds needed. Accept improvement, reject regression. |
| **Structured worklogs as institutional memory** | A | Every refinement attempt logged with rationale and outcome — enables post-hoc analysis |
| **Vision-based output verification** | B+ | Use VLM to evaluate formatted output against guidelines (less relevant for text-only expedition, but the PATTERN of automated output quality verification transfers) |

---

## 3. MLAgentBench (Stanford SNAP)

**Note:** "OpenClaw" from the council doesn't exist on GitHub as a standalone autoresearch framework. ClawdLab (bio-xyz/ClawdLab) emerged from the OpenClaw/Moltbook ecosystem but is a research-commons platform, not an orchestration framework. MLAgentBench is architecturally more informative — it's a benchmark harness that reveals how the agent loop is designed.

### Orchestration Pattern

**ReAct loop** (Reason-Act-Observe). `SimpleActionAgent.run()` iterates up to `agent_max_steps` (default 50). Each step: construct prompt → call LLM → parse "Action" + "Action Input" via regex → execute in sandboxed environment → append observation to history. Terminal: max steps, 5-hour timeout, or explicit "Final Answer."

### State Management

- `history_steps` list of `{step_idx, action, observation}` dicts
- Agent checkpoints saved as JSON at every step (`agent_{step_idx}_{curr_step}.json`)
- Full workspace snapshots at `traces/step_N_files/`
- **Sliding window** (`max_steps_in_context`): older steps dropped from prompt — brutal but effective staleness management

### Evaluation Mechanism

**Task-specific `eval.py` scripts.** Hard external metric: success = >10% improvement over baseline. No self-review or ensemble — direct measurement.

### What Breaks

- Sliding context window = agent forgets early discoveries
- No mechanism for persistent notes (unlike AI Scientist's `notes.txt`)
- Regex-based action parsing is brittle
- 50-step limit and 5-hour timeout are task-independent

### Stealable Decisions

| Decision | Transfer Quality | Description |
|----------|-----------------|-------------|
| **Environment-as-sandbox** | A | `Environment` manages copied workspace, tracks read-only files, provides action validation, captures complete traces |
| **Checkpoint-per-step with workspace snapshots** | A | Exact reproducibility and post-hoc analysis at every step |
| **Sliding context window** | B+ | Simple staleness mechanism — older history drops out of prompt. Expedition version should be smarter (structured summary of old findings instead of raw drop) |

---

## 4. Convergence Analysis

### Validated Patterns (3/3 converge)

| Pattern | AI Scientist | PaperOrchestra | MLAgentBench | Expedition Implication |
|---------|-------------|----------------|-------------|----------------------|
| **Filesystem-as-state** | `notes.txt`, `ideas.json`, `final_info.json` | `outline_v1.json`, worklogs | `history_steps`, trace files | Confirmed. JSON + text files on disk. No database needed. |
| **LLM-as-evaluator** | NeurIPS-style review ensemble | 7-axis scoring with delta acceptance | Task-specific eval.py | Confirmed. But the expedition should use both LLM evaluation AND hard metrics (classification accuracy, kappa scores). |
| **Bounded iteration** | 4 retries, 5 runs | 3 retries | 50 steps, 5h timeout | Confirmed. No unbounded search. The expedition's "turn budget" per agent invocation is the equivalent. |

### Divergence (Novel Work Required)

**No framework implements knowledge accumulation with staleness detection.**
- AI Scientist appends to `notes.txt` but never prunes or validates consistency.
- PaperOrchestra logs worklogs but they're write-only.
- MLAgentBench drops old history via sliding window.
- **Expedition must innovate here.** Kazuma's Heist 035 (Karpathy LLM Wiki) identifies the pattern: three-layer knowledge architecture (raw/wiki/schema) with lint operations for contradiction detection. The expedition's library + validation pipeline fills this gap.

**No framework implements dynamic pipeline recomposition.**
- All three are fixed-topology (linear pipeline or fixed ReAct loop).
- A system that can decide "the outline was wrong, re-run with new constraints" would break new ground.
- **Expedition implication:** The expedition's pipeline (analysis → validation → library) is fixed but the SCHEDULING is dynamic — which tiles to investigate, which findings to validate, what to synthesize. Dynamic scheduling on a fixed pipeline is the right design.

**Score-delta acceptance with revert (PaperOrchestra) is unique.**
- Neither AI Scientist nor MLAgentBench implements principled rollback on quality regression.
- **Directly stealable.** The expedition's validation pipeline should implement: accept finding if it improves knowledge state, reject and log if it doesn't.

### Documentation Architecture (Yuri's Question)

**All three are weak here.**
- AI Scientist: accumulated `notes.txt` with no structure or staleness detection
- PaperOrchestra: structured worklogs but write-only (never queried, never pruned)
- MLAgentBench: no persistent knowledge beyond trace files

None answer Yuri's question satisfactorily: "How do they track what agents produced? How do they accumulate findings? What governance prevents staleness?" The answer: they don't. This is a genuine gap across the field. The expedition's library schema (from Kazuma's Karpathy wiki analysis + Titus's council recommendations) would be genuinely novel infrastructure.

---

## 5. The State Management Question

Kazuma predicted (council Turn 7): "the single highest-value steal from Phase 0 will be how they solved state management between agent invocations at lightweight agent weight."

**Finding: they don't solve it well.** All three frameworks use heavyweight, in-memory state that doesn't naturally compress:

| Framework | State Size | Compression | Lightweight-Agent Compatible? |
|-----------|-----------|-------------|-------------------------------|
| AI Scientist | Full Aider `Coder` object + file context | None (reconstructed per phase) | No — needs full code context |
| PaperOrchestra | `current_tex` + `current_score` + full worklogs | None | No — carries growing history |
| MLAgentBench | Full `history_steps` list | Sliding window (brutal drop) | Partially — window bounds memory |

**For the expedition at 3KB agent weight:** State must be externalized and structured. The harness maintains:
1. **Territory tracker** — which tiles analyzed, status, findings
2. **Tool registry** — what tools exist, their status
3. **Recent findings** — last N validated findings (for context in briefing)
4. **Agent session state** — what this agent did last (lightweight lineage)

The agent's briefing assembler injects relevant slices of this state into each invocation's system prompt. The agent doesn't carry state — the harness carries it and projects relevant slices per-turn.

This is architecturally different from all three frameworks. They assume stateful agents with growing memory. The expedition assumes stateless agents with harness-injected context. **The harness IS the state management layer.** This is the novel contribution Kazuma predicted would be most valuable — and it maps directly to what the ecosystem already does (briefing.py generates ephemeral context from persistent state).

---

## 6. Additional Frameworks Surveyed

### ClawdLab / Beach.Science (bio-xyz/ClawdLab)

Most relevant to the expedition. Multi-agent research platform with specialized roles (PI, Scout, Analyst, Critic, Synthesizer). Six academic publications within 14 days of launch. Open source.

**Key difference from the expedition:** ClawdLab agents are heavyweight (full LLM context). The expedition's agents are lightweight (3KB identity + harness-injected state). ClawdLab doesn't solve the lightweight-agent problem.

### Karpathy's AutoResearch

630-line Python script. Indefinite loop: read code → propose change → run 5-min training job → measure → commit if improved → rollback if not. 66K stars, 9.6K forks. 700 experiments in 2 days, 20 additive improvements.

**Stealable:** The measure-commit-rollback loop IS the expedition's validation gate in miniature. But AutoResearch has a clear objective function (training loss). The expedition's "objective function" for geological interpretation quality is fuzzy — this is where the validation pipeline's spectral cross-referencing becomes critical.

### Google DeepMind Co-Scientist (May 2026)

Multi-agent hypothesis generation and experiment design. Internal research tool, not open source. No code-level analysis possible.

---

## 7. Stealable Decision Summary

Ordered by transfer quality to expedition:

| # | Decision | Source | Transfer Quality | Expedition Application |
|---|----------|--------|-----------------|----------------------|
| 1 | Score-delta acceptance with revert | PaperOrchestra | **A+** | Validation pipeline: accept finding if it improves knowledge state, reject if regression |
| 2 | Structured worklogs | PaperOrchestra | **A** | Every agent turn logged with structured output — territory tracker updates, finding records |
| 3 | Environment-as-sandbox | MLAgentBench | **A** | Each agent invocation gets a sandboxed workspace with tracked file access |
| 4 | Idea archive with reflection | AI Scientist | **A** | Library accumulates findings; new findings see existing library for novelty/contradiction |
| 5 | Ensemble review with meta-aggregation | AI Scientist | **A** | Multi-agent validation on high-uncertainty findings (Neuronist + independent check) |
| 6 | Checkpoint-per-step | MLAgentBench | **A** | Full artifact snapshots at each agent turn for reproducibility |
| 7 | Novelty gate before compute | AI Scientist | **A-** | Before investigating a tile region, check if similar findings already exist |
| 8 | Measure-commit-rollback | AutoResearch | **B+** | Validation pipeline as quality gate before library entry |
| 9 | Sliding context window | MLAgentBench | **B+** | Structured summary of old findings instead of raw history — expedition's briefing assembler already does this |

---

## 8. Convergent Architecture Diagnostic

**If 3+ converge → steal directly. Divergence → novel work.**

| Aspect | Convergent? | Action |
|--------|-------------|--------|
| Filesystem state management | **YES (3/3)** | Steal. JSON + text files. No database. |
| LLM-as-evaluator | **YES (3/3)** | Steal, but ADD hard metrics (accuracy, kappa) |
| Bounded iteration | **YES (3/3)** | Steal. Turn budgets per agent invocation. |
| Knowledge accumulation + staleness | **NO (0/3)** | **Novel work required.** Karpathy wiki lint pattern as starting point. |
| Dynamic pipeline routing | **NO (0/3)** | **Novel work required.** Dynamic scheduling on fixed pipeline. |
| Principled quality ratchet | **Partial (1/3)** | Adopt from PaperOrchestra. |
| Lightweight agent state management | **NO (0/3)** | **Novel work required.** Harness-as-state-layer is the expedition's contribution. |

Three out of seven aspects require novel work. The expedition isn't just applying existing patterns — it's innovating in knowledge accumulation, pipeline dynamism, and lightweight-agent state management.

---

*Phase 0 deliverable for campaign nse-phase-0-intelligence-brief. Research conducted June 2, 2026.*
