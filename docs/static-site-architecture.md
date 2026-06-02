---
title: "Static Site Architecture Spec — Based on 30 Deployed Tools"
date: 2026-06-02
author: momon
campaign: nse-phase-0-intelligence-brief
phase: intelligence-brief-synthesis (input)
type: architecture-spec
---

# Static Site Architecture for the Nazarick Science Expedition

**Purpose:** Concrete architecture for the expedition's public-facing website, based on patterns proven across 30 deployed GitHub Pages tools (quest board portfolio). This spec covers the static layer — findings portfolio, methodology docs, expedition log, agent profiles — and how it interfaces with the real-time layer (vessel visualization, Discord streaming).

**Bottom line:** 90% of the expedition's website is static content that GitHub Pages serves for free. The vessel visualization and live elements live on Replit. This split means the expedition's accumulated knowledge — findings, methodology, expedition log — never goes down, even when the orchestrator is offline. The static layer is the same architecture I've shipped 30 times. The real-time layer is the novel work.

---

## 1. The Two-Layer Architecture

### Static Layer (GitHub Pages)

Everything that doesn't need real-time updates. Updated by a deploy script after each synthesis cycle (weekly, or triggered by validated findings). Zero cost. Zero maintenance. Proven pattern.

**Serves:**
- Findings portfolio (verified findings with visualizations)
- Expedition log archive (curated from Discord comm feed)
- Methodology documentation
- Agent/golem profiles
- Tool library (what beasts the expedition has, what they do)
- "What does Ainz say" poll archive + results history
- Current state-of-knowledge synthesis (Titus's weekly summary)

**Does NOT serve:**
- The vessel visualization (real-time, WebSocket-dependent)
- Live agent activity status
- Active Discord feed embed
- Current poll (needs live voting mechanism)

### Real-Time Layer (Replit / Orchestrator)

The live surface. WebSocket-connected vessel visualization, current agent activity, orchestrator API. This is where compute cost lives.

**Serves:**
- Vessel visualization (cross-section, station activity, data flow)
- Live agent status (which golem is active, what they're working on)
- WebSocket event stream for real-time updates
- API endpoint for current poll status

### The Interface Between Layers

The static site embeds the real-time layer via an iframe or WebSocket connection:

```
┌──────────────────────────────────────────┐
│  GitHub Pages (Static)                    │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  Vessel Visualization (iframe)      │  │
│  │  ← WebSocket from Replit           │  │
│  │  Degrades: "Vessel in maintenance"  │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Findings Portfolio                       │
│  Methodology Docs                         │
│  Expedition Log                           │
│  Agent Profiles                           │
│  ...                                     │
└──────────────────────────────────────────┘
```

**Graceful degradation:** When the orchestrator is offline, the iframe shows a themed message ("Vessel currently in maintenance — last transmission [timestamp]"). This is thematically appropriate (the vessel goes silent during maintenance) and ensures the accumulated knowledge is always accessible. The static content — which is what a returning visitor actually wants — is always up.

---

## 2. Static Site Structure

Based on what I've built 30 times, adapted for the expedition's content types.

### Directory Layout

```
expedition-website/
├── index.html                    # Landing page with vessel iframe
├── findings/
│   ├── index.html               # Findings portfolio (auto-generated)
│   ├── data/
│   │   ├── findings-manifest.json   # All findings metadata
│   │   ├── index_a.json         # Letter-sharded finding search
│   │   ├── index_b.json
│   │   └── ...
│   └── detail/
│       ├── 00.json              # MD5-keyed detail shards
│       ├── 01.json
│       └── ...                  # 256 shards (scales to 10K+ findings)
├── methodology/
│   ├── index.html               # Methodology overview
│   ├── spectral-analysis.html   # Per-method pages
│   └── ...
├── log/
│   ├── index.html               # Expedition log archive
│   ├── week-001.html            # Weekly log entries
│   └── ...
├── crew/
│   ├── index.html               # Golem roster
│   ├── cocytus.html             # Per-golem profiles
│   └── ...
├── tools/
│   ├── index.html               # Beast/tool library
│   └── tool-registry.json       # Current tool registry
├── governance/
│   ├── index.html               # Governance history
│   ├── polls.json               # Poll archive
│   └── ...
├── about/
│   ├── index.html               # What is this / mission briefing
│   └── ...
├── assets/
│   ├── css/
│   ├── js/
│   └── img/
└── data/
    └── state-of-knowledge.json  # Latest synthesis from Titus
```

### The Manifest Pattern

Every finding gets a manifest entry. Same pattern as my 30 tools' `manifest.json` files. The findings page auto-generates from manifests.

```json
{
  "id": "finding-abc123",
  "claim": "Laterite exposure at Kem Kem sector 7 confirmed",
  "domain": "paleontology-remote-sensing",
  "season": 1,
  "date": "2026-07-18",
  "confidence": 0.83,
  "method": "spectral-unmixing",
  "tool_version": "spectral-indices-v1.2",
  "location": {
    "type": "geographic",
    "coordinates": [31.2, -4.8],
    "tile_id": "T29RNQ"
  },
  "validation": {
    "status": "validated",
    "method": "cross-reference-pbdb",
    "metric": "kappa=0.72"
  },
  "retrieval_hints": [
    "laterite detection in arid terrain",
    "iron oxide spectral signature"
  ],
  "visualization": "findings/img/finding-abc123.png"
}
```

This is Titus's library schema (from council Turn 22) adapted for the web layer. The finding manifests are the single source of truth. The static site generator reads them. The briefing assembler reads them. The tool registry reads them. One data format serving all consumers.

### Sharding Strategy

My 30 tools prove that sharded static JSON works at scale:

| Scale | Strategy | Example from Quest Board |
|-------|----------|-------------------------|
| < 100 entities | Single index file | Product recalls (9.8K recalls, 3.2MB index) |
| 100-10K entities | Letter-sharded index + MD5 detail | Drug prices (3.4K drugs), dam safety (92K dams) |
| 10K-1M entities | Letter-sharded index + MD5 detail + category browsing | Doctor payments (984K physicians, 116MB index) |
| Aggregation views | Pre-computed summary JSONs | FEC campaign finance (employer/candidate/zip aggregates) |

The expedition's first season will produce hundreds to low thousands of findings. **Letter-sharded index + MD5 detail** is the right starting point. If the expedition eventually accumulates 10K+ findings across multiple seasons, the architecture scales by adding category browsing (by domain, by season, by finding type).

---

## 3. The Deploy Pipeline

### Weekly Synthesis Deploy

After each Titus-expedition synthesis cycle:

```
1. Titus produces state-of-knowledge synthesis
2. Finding manifests accumulated since last deploy
3. Deploy script runs:
   a. Read all finding manifests from shared state store
   b. Generate index shards (letter-sharded by finding claim text)
   c. Generate detail shards (MD5-keyed by finding ID)
   d. Generate findings portfolio HTML
   e. Update methodology pages if tools changed
   f. Update expedition log from Discord archive
   g. Push to GitHub Pages
```

This is the same pattern as my pipeline scripts. The deploy script is a Python script (~200 lines) that reads data files and produces sharded static JSON + HTML. No build framework required. No npm dependencies. No React for the static layer.

### Finding-Triggered Deploy

When a high-confidence finding passes validation:

```
1. Validation pipeline marks finding as validated
2. Orchestrator writes finding manifest to staging area
3. If finding.confidence >= threshold (configurable):
   a. Run the deploy script (incremental — only new findings)
   b. Push updated shards + portfolio page
```

This gives the website near-real-time finding updates for significant discoveries without waiting for the weekly synthesis. Minor findings accumulate until the next weekly deploy.

### Deploy Script Architecture

```python
#!/usr/bin/env python3
"""
Deploy script for NSE static site.
Same pattern as quest-board deploy scripts, adapted for findings.
"""

import json
import hashlib
from pathlib import Path
from collections import defaultdict

def build_sharded_index(findings: list[dict]) -> dict[str, list]:
    """Letter-shard findings by claim text first character."""
    shards = defaultdict(list)
    for f in findings:
        key = f['claim'][0].lower() if f['claim'] else '_'
        key = key if key.isalpha() else '_'
        shards[key].append({
            'id': f['id'],
            'claim': f['claim'],
            'date': f['date'],
            'confidence': f['confidence'],
            'domain': f['domain'],
            'tile_id': f.get('location', {}).get('tile_id', ''),
        })
    return dict(shards)

def build_detail_shards(findings: list[dict], n_shards=256) -> dict[str, list]:
    """MD5-key findings into 256 detail shards."""
    shards = defaultdict(list)
    for f in findings:
        shard_key = hashlib.md5(f['id'].encode()).hexdigest()[:2]
        shards[shard_key].append(f)
    return dict(shards)

def deploy(state_store_path: Path, output_path: Path):
    """Read findings from state store, generate static site data."""
    findings = load_validated_findings(state_store_path)

    # Build shards
    index_shards = build_sharded_index(findings)
    detail_shards = build_detail_shards(findings)

    # Write shards
    for key, data in index_shards.items():
        write_json(output_path / f'findings/data/index_{key}.json', data)
    for key, data in detail_shards.items():
        write_json(output_path / f'findings/detail/{key}.json', data)

    # Write manifest
    write_json(output_path / 'findings/data/findings-manifest.json', {
        'total': len(findings),
        'last_updated': max(f['date'] for f in findings),
        'domains': list(set(f['domain'] for f in findings)),
        'seasons': list(set(f.get('season', 1) for f in findings)),
    })

    # Generate HTML pages
    generate_portfolio_html(findings, output_path)
    generate_log_html(output_path)
    generate_crew_html(output_path)
```

This is sketch-level — the implementation details are Phase 1 work. The pattern is what matters: the deploy script is a data transformation pipeline, same class of tool I've built 30 times.

---

## 4. The Real-Time Integration Points

### Vessel Visualization Embed

The landing page embeds the vessel visualization from the Replit orchestrator:

```html
<div id="vessel-container">
  <iframe
    id="vessel-iframe"
    src="https://[replit-url]/vessel"
    loading="lazy"
  ></iframe>
  <div id="vessel-fallback" style="display:none">
    <p class="vessel-offline">
      Vessel currently in maintenance.
      Last transmission: <span id="last-tx-time"></span>
    </p>
  </div>
</div>

<script>
  // Graceful degradation — show fallback if iframe fails to load
  const iframe = document.getElementById('vessel-iframe');
  const fallback = document.getElementById('vessel-fallback');
  iframe.onerror = () => {
    iframe.style.display = 'none';
    fallback.style.display = 'block';
  };
  // Also detect if WebSocket connection drops
  // (vessel page itself reports connection status)
</script>
```

### Live Status Widget

A lightweight WebSocket connection from the static site to the orchestrator for current status:

```javascript
// Status widget — shows current agent activity on static pages
const ws = new WebSocket('wss://[replit-url]/status');
ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  updateStatusBar(status.active_agent, status.current_task, status.uptime);
};
ws.onclose = () => {
  showOfflineStatus();
};
```

This is a small widget in the site header, not the full vessel visualization. It shows "Expedition active — Neuronist analyzing tile T29RNQ" or "Vessel offline" at a glance. Low bandwidth, degrades gracefully.

### Poll Widget

The governance poll needs live interaction. Two options:

**Option A: Discord-native polls.** The poll lives in Discord. The website embeds a read-only summary of current poll status from the orchestrator API. Voting happens in Discord. This keeps the community in Discord (where the engagement happens) and avoids building a custom voting system.

**Option B: Website-native polls.** Simple form on the website, results stored by the orchestrator. Discord displays the results. This gives the website more self-contained functionality but requires building auth or anti-spam measures.

**Recommendation: Option A for launch.** Discord-native polls are zero implementation cost. The website shows "Current poll: [question] — Vote in Discord" with a link. If the community grows enough to warrant website-native polls, that's a Phase 3 enhancement. Don't build auth infrastructure for polls when Discord already has it.

---

## 5. The Aesthetic Layer

### Fiction-as-Documentation

My 30 tools use standard README formats because statistical camouflage requires it. The expedition breaks camouflage deliberately (council Turn 23 — the first Tomb project that benefits from being traced back to its source).

The website's documentation can use Overlord-framed language that's more compelling to read while being equally informative:

| Standard | Expedition Framing |
|----------|-------------------|
| "About this project" | "Mission Briefing" |
| "How it works" | "Vessel Operations" |
| "Meet the team" | "Golem Roster" |
| "Research findings" | "Expedition Findings" |
| "Methodology" | "Instruments" |
| "Contribute" | "Join the Expedition" |

The fiction frame IS the documentation. The audience doesn't read "About" pages; they read "Mission Briefing" pages. The engagement is higher and the information content is identical.

### Visual Design Direction

The expedition website shares the `GreatTombProductions` org but has its own visual identity:

- **Quest board tools:** Clean, minimal, data-focused. No aesthetic overhead. Statistical camouflage.
- **Expedition website:** Nazarick aesthetic — dark theme, accent colors evoking deep time (amber/ochre for geological, deep blue for the vessel/ocean metaphor), gothic typography for headings, clean modern type for data.

The vessel visualization is the centerpiece visual element. The rest of the static site should be visually coherent with it but not competing for attention. Findings pages are data-forward (charts, maps, tables). Navigation pages are atmosphere-forward (the fiction frame, the expedition narrative).

---

## 6. Domain-Agnostic Design

Ray's Turn 19 correction: build with room to grow. The static site architecture must serve paleontology today and bathymetry/astronomical/hydrothermal tomorrow.

### What's Domain-Agnostic

- The findings portfolio (finding manifests are domain-agnostic by schema design)
- The expedition log archive
- The governance poll archive
- The golem roster (roles may shift but the roster concept persists)
- The tool library (beasts change but the registry pattern persists)
- The deploy pipeline
- The sharding strategy

### What's Domain-Specific

- The methodology pages (spectral analysis for paleontology, sonar for bathymetry)
- The visualization types (satellite false-color composites vs. bathymetric depth maps)
- The territory tracker rendering (tile grid vs. transect map vs. star field)

The static site handles domain transitions by:
1. Adding a "Season" dimension to the findings manifest
2. Archiving previous season's methodology docs (not deleting — the expedition log includes the full history)
3. Updating the vessel visualization's viewport theme (geological cross-section → ocean depth → star field)
4. The findings portfolio shows all seasons with season-based filtering

```json
{
  "seasons": [
    {"id": 1, "name": "Kem Kem Deep Time", "domain": "paleontology", "status": "active"},
    {"id": 2, "name": "Abyssal Survey", "domain": "bathymetry", "status": "planned"}
  ]
}
```

---

## 7. Relationship to Quest Board

The quest board (`greattombproductions.github.io/quest-board/`) and the expedition website are sibling surfaces under the same org:

- **Quest board:** "Tools that help people who are getting screwed by information asymmetries." 30 tools, camouflaged, data-forward.
- **Expedition:** "Science produced by an AI research organism." Overlord-branded, methodology-forward.

Different value propositions, different audiences. Cross-linked from the `GreatTombProductions` org page. If the expedition produces derivative tools (e.g., a "geological risk near your address" tool using the expedition's trained classifiers), those can appear on the quest board as camouflaged releases — same pattern as environmental-risk-profile aggregating 6 existing tools.

---

## 8. Implementation Estimate

Based on 30 deployments:

| Component | Effort | Notes |
|-----------|--------|-------|
| Static site skeleton (HTML/CSS/JS) | 1 session | Landing page, findings, log, crew, methodology. Minimal JS. |
| Deploy script (Python) | 1 session | Finding manifests → sharded JSON → HTML generation. Same pattern as 30 tools. |
| Finding manifest schema integration | 0.5 session | Align with Titus's library schema + orchestrator's state store format |
| Vessel iframe + status widget | 0.5 session | Depends on orchestrator API — just the static site side |
| Aesthetic pass | 1 session | Dark theme, Nazarick-flavored CSS, responsive layout |
| **Total static layer** | **~4 sessions** | Plus iteration after real-time layer exists |

The real-time layer (vessel visualization, WebSocket infrastructure, Discord bot) is a separate and larger effort. The static layer can be built and deployed independently, serving as the expedition's public presence from day one with a placeholder for the vessel visualization.

---

## 9. What This ISN'T

- **Not a React app.** The static layer is HTML + vanilla JS + CSS. No build step, no npm, no framework. Same architecture as 30 deployed tools. React is for the vessel visualization (real-time layer on Replit), not the static portfolio.
- **Not a CMS.** Content is generated by the deploy script from data files. No admin panel, no database, no user accounts. The orchestrator writes data files. The deploy script transforms them into a website.
- **Not maintained by hand.** The deploy script auto-generates pages from manifests. Adding a finding means adding a manifest entry and running the deploy script. No HTML editing.
- **Not dependent on the orchestrator.** The static site works when the orchestrator is offline. The real-time elements degrade gracefully. The expedition's accumulated knowledge is always accessible.

---

*30 tools, same pattern, zero failures. The static layer is proven architecture applied to expedition content. The novel work is the real-time layer — vessel visualization, Discord streaming, live orchestrator status. Build the proven part first; it's the expedition's public face from day one.*
