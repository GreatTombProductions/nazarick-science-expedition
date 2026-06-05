/**
 * Vessel Visualization — Agnostophage Cross-Section
 * FILE_TRAJECTORY: load-bearing
 * Real-time SVG visualization of the NSE research vessel.
 * Vanilla JS, no dependencies. Connects to orchestrator WebSocket.
 */
(function () {
  'use strict';

  // Layout
  const VB = { w: 920, h: 400 };
  const HULL = { x: 20, y: 10, w: 880, h: 380, r: 8 };
  const DH = 90; // deck height
  const DECKS = {
    command: { y: 10, label: 'Command' },
    science: { y: 100, label: 'Science' },
    archive: { y: 190, label: 'Archive' },
    engine:  { y: 280, label: 'Engine' },
  };
  const STAGE_DIR = { acquire: 0, analyze: 90, validate: 180, synthesize: 270, maintain: 45 };
  const TIER_CLR = { STRONG: '#22c55e', PRELIMINARY: '#eab308', NEGATIVE: '#ef4444', TECHNICAL: '#8b5cf6' };
  const MOROCCO = [[-1,35.8],[-2.2,35.1],[-3.8,33.9],[-5.6,33.9],[-6.8,33.4],[-8.7,33.3],[-9.8,32.3],[-9.8,30.4],[-10,29.4],[-10,28.7],[-12.8,27.7],[-13.2,27.7],[-13,26],[-12,25.4],[-12,23.5],[-14.4,22.5],[-17.1,21],[-17.1,25.2],[-16,27.2],[-13.2,29.2],[-10.6,29.8],[-9.2,31.6],[-7.4,33.2],[-5.1,35.7],[-2.2,36.8],[-1,35.8]];
  const NS = 'http://www.w3.org/2000/svg';

  // State
  let state = {
    orchestrator_status: 'idle', current_stage: null,
    active_agents: [],
    pipeline_state: { stages: ['acquire','analyze','validate','synthesize','maintain'].map(n => ({ name: n, status: 'pending' })) },
    findings_summary: { total: 0, by_tier: { STRONG: 0, PRELIMINARY: 0, NEGATIVE: 0, TECHNICAL: 0 }, timeline: [] },
    tool_health: [], current_tile: null, activity_log: [],
  };
  let ws = null, wsRetries = 0, wsTimer = null, lastEvt = null, staleTimer = null;
  let activeDeckMobile = 'command', rMode = 'full';
  let svgEl, rootEl;
  const R = {}; // element refs

  // Helpers
  function $(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
    if (parent) parent.appendChild(e);
    return e;
  }
  function txt(s, attrs, parent) { const t = $(('text'), attrs, parent); t.textContent = s; return t; }
  function trunc(s, n) { return !s ? '' : s.length > n ? s.slice(0, n - 1) + '\u2026' : s; }
  function escH(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }
  function clr(el) { while (el.firstChild) el.removeChild(el.firstChild); }
  function byId(id) { return document.getElementById(id); }

  // SVG Scaffold
  function createSVG() {
    const svg = $('svg', { viewBox: `0 0 ${VB.w} ${VB.h}`, preserveAspectRatio: 'xMidYMid meet', xmlns: NS });

    // Hull
    $('rect', { x: HULL.x, y: HULL.y, width: HULL.w, height: HULL.h, rx: HULL.r, fill: '#12121a', stroke: '#2a2a3a', 'stroke-width': 1.5 }, svg);

    // Deck separators
    for (let i = 1; i < 4; i++) {
      const sy = HULL.y + DH * i;
      $('line', { x1: HULL.x + 8, y1: sy, x2: HULL.x + HULL.w - 8, y2: sy, stroke: '#2a2a3a', 'stroke-width': 1, 'stroke-dasharray': '4,4' }, svg);
    }

    // Deck labels
    for (const [k, d] of Object.entries(DECKS))
      txt(d.label, { x: HULL.x + 15, y: d.y + 15, class: 'vessel-deck-title' }, svg);

    // === Command Deck ===
    const cmdG = $('g', { id: 'deck-command' }, svg);

    // Compass
    const cmpG = $('g', { id: 'station-compass', class: 'vessel-interactive', transform: `translate(${HULL.x + 80}, ${DECKS.command.y + 42})` }, cmdG);
    $('circle', { cx: 25, cy: 25, r: 24, fill: '#1a1a25', stroke: '#2a2a3a', 'stroke-width': 1 }, cmpG);
    for (const [l, x, y] of [['N',25,8],['S',25,46],['E',46,28],['W',4,28]])
      txt(l, { x, y, 'text-anchor': 'middle', 'font-size': '7', fill: '#555568' }, cmpG);
    R.needle = $('line', { x1: 25, y1: 25, x2: 25, y2: 6, stroke: '#8b5cf6', 'stroke-width': 2, 'stroke-linecap': 'round', class: 'vessel-compass-needle' }, cmpG);
    txt('Compass', { x: 25, y: -4, 'text-anchor': 'middle', class: 'vessel-label' }, cmpG);

    // Activity Feed
    const feedG = $('g', { id: 'station-feed', transform: `translate(${HULL.x + 220}, ${DECKS.command.y + 22})` }, cmdG);
    $('rect', { x: 0, y: 0, width: 400, height: 60, rx: 4, fill: '#12121a', stroke: '#2a2a3a', 'stroke-width': 0.5 }, feedG);
    txt('Activity Feed', { x: 5, y: -4, class: 'vessel-label' }, feedG);
    R.feedLines = [];
    for (let i = 0; i < 5; i++) R.feedLines.push(txt('', { x: 8, y: 14 + i * 11, class: 'vessel-feed-line' }, feedG));

    // Status Orb
    const orbG = $('g', { id: 'station-orb', class: 'vessel-interactive', transform: `translate(${HULL.x + 740}, ${DECKS.command.y + 42})` }, cmdG);
    txt('Status', { x: 25, y: -4, 'text-anchor': 'middle', class: 'vessel-label' }, orbG);
    R.orb = $('circle', { cx: 25, cy: 25, r: 20, class: 'vessel-orb vessel-orb--idle' }, orbG);

    // === Science Deck ===
    const sciG = $('g', { id: 'deck-science' }, svg);

    // Spectral Lab
    const labG = $('g', { id: 'station-lab', transform: `translate(${HULL.x + 80}, ${DECKS.science.y + 20})` }, sciG);
    $('rect', { x: 0, y: 0, width: 240, height: 60, rx: 4, fill: '#1a1a25', stroke: '#2a2a3a', 'stroke-width': 0.5 }, labG);
    txt('Spectral Lab', { x: 5, y: -4, class: 'vessel-label' }, labG);
    R.labSlots = [];
    for (let i = 0; i < 4; i++) {
      const sg = $('g', { class: 'vessel-station vessel-station--idle vessel-interactive', transform: `translate(${20 + i * 55}, 10)`, 'data-station': `lab-${i}` }, labG);
      $('circle', { cx: 20, cy: 20, r: 18, class: 'vessel-station-bg' }, sg);
      const ini = txt('', { x: 20, y: 20, class: 'vessel-station-initials' }, sg);
      R.labSlots.push({ g: sg, ini });
    }

    // Validation Chamber
    const valG = $('g', { id: 'station-validation', class: 'vessel-station vessel-station--idle vessel-interactive', transform: `translate(${HULL.x + 360}, ${DECKS.science.y + 20})`, 'data-station': 'validation' }, sciG);
    $('rect', { x: 0, y: 0, width: 200, height: 60, rx: 4, class: 'vessel-station-bg' }, valG);
    txt('Validation', { x: 5, y: -4, class: 'vessel-label' }, valG);
    R.valVerdict = txt('', { x: 100, y: 35, 'text-anchor': 'middle', 'font-size': '11', fill: '#8888a0', 'font-family': "'JetBrains Mono', monospace" }, valG);
    R.valG = valG;

    // Tile Inset
    const tileG = $('g', { id: 'station-tile', class: 'vessel-interactive', transform: `translate(${HULL.x + 620}, ${DECKS.science.y + 20})`, 'data-station': 'tile' }, sciG);
    $('rect', { x: 0, y: 0, width: 200, height: 60, rx: 4, fill: '#12121a', stroke: '#2a2a3a', 'stroke-width': 0.5 }, tileG);
    txt('Current Tile', { x: 5, y: -4, class: 'vessel-label' }, tileG);
    const morG = $('g', { transform: 'translate(5, 5)' }, tileG);
    // Morocco outline
    const iW = 190, iH = 50, lonR = [-17.1, -1], latR = [21, 36.8];
    const pts = MOROCCO.map(([lo, la]) => `${(((lo - lonR[0]) / (lonR[1] - lonR[0])) * iW).toFixed(1)},${(((latR[1] - la) / (latR[1] - latR[0])) * iH).toFixed(1)}`).join(' ');
    $('polyline', { points: pts, class: 'vessel-morocco-outline' }, morG);
    R.tileHL = $('rect', { x: 0, y: 0, width: 0, height: 0, class: 'vessel-tile-highlight', style: 'display:none' }, morG);

    // === Archive Deck ===
    const arcG = $('g', { id: 'deck-archive' }, svg);

    // Finding Shelves
    const shG = $('g', { id: 'station-shelves', class: 'vessel-interactive', transform: `translate(${HULL.x + 80}, ${DECKS.archive.y + 20})`, 'data-station': 'shelves' }, arcG);
    $('rect', { x: 0, y: 0, width: 480, height: 60, rx: 4, fill: '#12121a', stroke: '#2a2a3a', 'stroke-width': 0.5 }, shG);
    txt('Finding Shelves', { x: 5, y: -4, class: 'vessel-label' }, shG);
    R.shelvesBox = $('g', { transform: 'translate(10, 10)' }, shG);
    R.shelvesCount = txt('0 findings', { x: 10, y: 52, class: 'vessel-value', 'font-size': '10' }, shG);

    // Evolution Sparkline
    const evoG = $('g', { id: 'station-evolution', transform: `translate(${HULL.x + 620}, ${DECKS.archive.y + 20})` }, arcG);
    $('rect', { x: 0, y: 0, width: 200, height: 60, rx: 4, fill: '#12121a', stroke: '#2a2a3a', 'stroke-width': 0.5 }, evoG);
    txt('Evolution', { x: 5, y: -4, class: 'vessel-label' }, evoG);
    R.spark = $('g', { transform: 'translate(10, 8)' }, evoG);

    // === Engine Room ===
    const engG = $('g', { id: 'deck-engine' }, svg);

    // Pipeline
    const pipG = $('g', { id: 'station-pipeline', transform: `translate(${HULL.x + 80}, ${DECKS.engine.y + 20})` }, engG);
    $('rect', { x: 0, y: 0, width: 380, height: 60, rx: 4, fill: '#12121a', stroke: '#2a2a3a', 'stroke-width': 0.5 }, pipG);
    txt('Pipeline', { x: 5, y: -4, class: 'vessel-label' }, pipG);
    R.pipeNodes = {};
    const stages = ['acquire', 'analyze', 'validate', 'synthesize', 'maintain'];
    stages.forEach((nm, i) => {
      const cx = 20 + i * 70, cy = 35;
      if (i < 4) $('line', { x1: cx + 10, y1: cy, x2: cx + 60, y2: cy, stroke: '#2a2a3a', 'stroke-width': 1 }, pipG);
      const ng = $('g', { class: 'vessel-pipeline-node vessel-pipeline-node--pending', 'data-stage': nm }, pipG);
      $('circle', { cx, cy, r: 8 }, ng);
      txt(nm.slice(0, 3).toUpperCase(), { x: cx, y: cy + 20, 'text-anchor': 'middle', 'font-size': '7', fill: '#555568', 'font-family': "'JetBrains Mono', monospace" }, ng);
      R.pipeNodes[nm] = ng;
    });

    // Tool Registry
    const tlG = $('g', { id: 'station-tools', transform: `translate(${HULL.x + 520}, ${DECKS.engine.y + 20})` }, engG);
    $('rect', { x: 0, y: 0, width: 300, height: 60, rx: 4, fill: '#12121a', stroke: '#2a2a3a', 'stroke-width': 0.5 }, tlG);
    txt('Tool Registry', { x: 5, y: -4, class: 'vessel-label' }, tlG);
    R.toolBox = $('g', { transform: 'translate(10, 12)' }, tlG);

    // Particle layer
    R.particles = $('g', { id: 'particle-layer' }, svg);

    return svg;
  }

  // Dynamic Rendering
  function render() { renderOrb(); renderCompass(); renderFeed(); renderAgents(); renderPipeline(); renderFindings(); renderSparkline(); renderTools(); renderTile(); }

  function renderOrb() {
    if (!R.orb) return;
    R.orb.setAttribute('class', `vessel-orb vessel-orb--${state.orchestrator_status}`);
  }

  function renderCompass() {
    if (!R.needle) return;
    R.needle.setAttribute('transform', `rotate(${STAGE_DIR[state.current_stage] || 0}, 25, 25)`);
  }

  function renderFeed() {
    if (!R.feedLines) return;
    const log = state.activity_log.slice(-5);
    R.feedLines.forEach((ln, i) => {
      if (i < log.length) {
        const e = log[i];
        const ts = e.timestamp ? new Date(e.timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }) : '';
        const pfx = e.agent_id ? `[${e.agent_id}] ` : '';
        ln.textContent = trunc(`${ts} ${pfx}${e.text}`, 55);
      } else ln.textContent = '';
    });
    // Stale indicator
    if (state.orchestrator_status === 'idle' && state.activity_log.length > 0) {
      const last = new Date(state.activity_log[state.activity_log.length - 1].timestamp);
      const mins = (Date.now() - last.getTime()) / 60000;
      if (mins > 5 && R.feedLines[4]) R.feedLines[4].textContent = `No activity for ${Math.floor(mins)}m \u2014 vessel in observation mode`;
    }
  }

  function renderAgents() {
    const aa = state.active_agents.filter(a => a.stage === 'analyze' && a.status === 'active');
    R.labSlots.forEach((s, i) => {
      const a = aa[i];
      s.g.setAttribute('class', `vessel-station vessel-station--${a ? 'active' : 'idle'} vessel-interactive`);
      s.ini.textContent = a ? a.initials : '';
      if (a) { s.g.setAttribute('data-agent-id', a.agent_id); s.g.setAttribute('data-agent-role', a.role); }
      else s.g.removeAttribute('data-agent-id');
    });
    const va = state.active_agents.find(a => a.stage === 'validate' && a.status === 'active');
    if (R.valG) R.valG.setAttribute('class', `vessel-station vessel-station--${va ? 'active' : 'idle'} vessel-interactive`);
  }

  function renderPipeline() {
    for (const s of state.pipeline_state.stages) {
      const n = R.pipeNodes[s.name];
      if (n) n.setAttribute('class', `vessel-pipeline-node vessel-pipeline-node--${s.status}`);
    }
  }

  function renderFindings() {
    if (!R.shelvesBox) return;
    clr(R.shelvesBox);
    const sz = 10, gap = 3, maxR = Math.floor(460 / (sz + gap));
    let idx = 0;
    for (const tier of ['STRONG', 'PRELIMINARY', 'NEGATIVE', 'TECHNICAL']) {
      for (let i = 0; i < (state.findings_summary.by_tier[tier] || 0); i++, idx++) {
        const r = Math.floor(idx / maxR), c = idx % maxR;
        $('rect', { x: c * (sz + gap), y: r * (sz + gap), width: sz, height: sz, rx: 2, fill: TIER_CLR[tier], class: 'vessel-finding-square', 'data-tier': tier, 'data-index': idx }, R.shelvesBox);
      }
    }
    R.shelvesCount.textContent = `${state.findings_summary.total} finding${state.findings_summary.total !== 1 ? 's' : ''}`;
  }

  function renderSparkline() {
    if (!R.spark) return;
    clr(R.spark);
    const tl = state.findings_summary.timeline;
    if (!tl || tl.length < 2) return;
    const w = 180, h = 40, mx = Math.max(...tl.map(t => t.count), 1);
    const pts = tl.map((t, i) => `${((i / (tl.length - 1)) * w).toFixed(1)},${(h - (t.count / mx) * h).toFixed(1)}`);
    $('polygon', { points: `0,${h} ${pts.join(' ')} ${w},${h}`, class: 'vessel-sparkline-area' }, R.spark);
    $('polyline', { points: pts.join(' '), class: 'vessel-sparkline-path' }, R.spark);
  }

  function renderTools() {
    if (!R.toolBox) return;
    clr(R.toolBox);
    const bH = 8, bW = 180, gap = 4;
    state.tool_health.slice(0, 5).forEach((t, i) => {
      const y = i * (bH + gap);
      txt(trunc(t.name, 12), { x: 0, y: y + bH - 1, 'font-size': '8', fill: '#555568', 'font-family': "'JetBrains Mono', monospace" }, R.toolBox);
      $('rect', { x: 85, y, width: bW, height: bH, class: 'vessel-health-bar-bg' }, R.toolBox);
      $('rect', { x: 85, y, width: (t.uptime_pct / 100) * bW, height: bH, class: `vessel-health-bar-fill vessel-health-bar-fill--${t.status}`, 'data-tool': t.tool_id }, R.toolBox);
    });
  }

  function renderTile() {
    if (!R.tileHL) return;
    const t = state.current_tile;
    if (!t || !t.bbox) { R.tileHL.style.display = 'none'; return; }
    const [w, s, e, n] = t.bbox, iW = 190, iH = 50, lR = [-17.1, -1], aR = [21, 36.8];
    const lD = lR[1] - lR[0], aD = aR[1] - aR[0];
    R.tileHL.setAttribute('x', ((w - lR[0]) / lD) * iW);
    R.tileHL.setAttribute('y', ((aR[1] - n) / aD) * iH);
    R.tileHL.setAttribute('width', Math.max(((e - w) / lD) * iW, 3));
    R.tileHL.setAttribute('height', Math.max(((n - s) / aD) * iH, 3));
    R.tileHL.style.display = '';
  }

  // Animations
  function spawnParticle(fromDeck, toDeck) {
    if (!R.particles) return;
    const fY = (DECKS[fromDeck] ? DECKS[fromDeck].y : 10) + DH;
    const tY = (DECKS[toDeck] ? DECKS[toDeck].y : 190) + DH / 2;
    const x = HULL.x + 100 + Math.random() * (HULL.w - 200);
    const c = $('circle', { cx: x, cy: fY, r: 2.5, fill: '#8b5cf6', opacity: 0.8, class: 'vessel-particle' }, R.particles);
    const t0 = performance.now();
    (function frame(now) {
      const p = Math.min((now - t0) / 800, 1);
      const ease = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      c.setAttribute('cy', fY + (tY - fY) * ease);
      c.setAttribute('fill', `rgb(${Math.round(139 + (34 - 139) * p)},${Math.round(92 + (197 - 92) * p)},${Math.round(246 + (94 - 246) * p)})`);
      c.setAttribute('opacity', 0.8 - p * 0.3);
      p < 1 ? requestAnimationFrame(frame) : c.remove();
    })(t0);
  }

  function flashStation(el, finding) {
    if (!el) return;
    el.setAttribute('class', el.getAttribute('class').replace(/vessel-station--\w+/, `vessel-station--${finding ? 'complete-finding' : 'complete'}`));
    setTimeout(() => el.setAttribute('class', el.getAttribute('class').replace(/vessel-station--\w+/, 'vessel-station--idle')), 400);
  }

  // WebSocket
  function wsConnect() {
    const url = wsUrl();
    if (!url) { showOffline(); return; }
    try { ws = new WebSocket(url); } catch (e) { wsErr(); return; }
    ws.onopen = () => { wsRetries = 0; hide('vessel-overlay'); hide('vessel-offline'); };
    ws.onmessage = (ev) => { lastEvt = Date.now(); try { handleMsg(JSON.parse(ev.data)); } catch (e) {} };
    ws.onclose = () => { ws = null; wsRetries < 3 ? (show('vessel-overlay'), wsTimer = setTimeout(wsConnect, Math.min(1000 * Math.pow(2, wsRetries++), 30000))) : showOffline(); };
    ws.onerror = wsErr;
  }

  function wsErr() { if (ws) ws.close(); }

  function wsUrl() {
    const p = new URLSearchParams(window.location.search);
    if (p.get('ws')) return p.get('ws');
    const m = document.querySelector('meta[name="ws-endpoint"]');
    if (m) return m.content;
    const h = window.location.host;
    return h ? `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${h}/ws/vessel` : null;
  }

  function show(id) { const e = byId(id); if (e) e.classList.remove('vessel-overlay--hidden', 'vessel-offline-screen--hidden'); }
  function hide(id) { const e = byId(id); if (e) e.classList.add(id === 'vessel-overlay' ? 'vessel-overlay--hidden' : 'vessel-offline-screen--hidden'); }

  function showOffline() {
    show('vessel-offline');
    const ts = byId('vessel-offline-ts');
    if (ts && lastEvt) ts.textContent = `Last transmission: ${new Date(lastEvt).toLocaleString()}`;
  }

  // Message handling
  function handleMsg(m) {
    const h = {
      state_snapshot: () => { Object.assign(state, { orchestrator_status: m.orchestrator_status || 'idle', current_stage: m.current_stage, active_agents: m.active_agents || [], pipeline_state: m.pipeline_state || state.pipeline_state, findings_summary: m.findings_summary || state.findings_summary, tool_health: m.tool_health || [], current_tile: m.current_tile, activity_log: m.activity_log || [] }); render(); },
      agent_start: () => { const idx = state.active_agents.findIndex(a => a.agent_id === m.agent_id); const as = { agent_id: m.agent_id, role: m.agent_role, stage: m.stage, status: 'active', initials: (m.agent_id || '??').slice(0, 2).toUpperCase() }; idx >= 0 ? state.active_agents[idx] = as : state.active_agents.push(as); addLog(m.timestamp, m.agent_id, `${m.agent_role} started: ${m.detail || m.stage}`); renderAgents(); renderFeed(); },
      agent_complete: () => { state.active_agents = state.active_agents.filter(a => a.agent_id !== m.agent_id); addLog(m.timestamp, m.agent_id, `${m.agent_role} completed: ${m.detail || m.stage}`); const s = R.labSlots.find(s => s.g.getAttribute('data-agent-id') === m.agent_id); if (s) flashStation(s.g, false); if (m.stage === 'validate') flashStation(R.valG, false); renderAgents(); renderFeed(); },
      agent_error: () => { state.active_agents = state.active_agents.filter(a => a.agent_id !== m.agent_id); addLog(m.timestamp, m.agent_id, `ERROR: ${m.detail || 'error'}`); renderAgents(); renderFeed(); },
      finding_new: () => { state.findings_summary.total++; state.findings_summary.by_tier[m.tier || 'PRELIMINARY'] = (state.findings_summary.by_tier[m.tier || 'PRELIMINARY'] || 0) + 1; addLog(m.timestamp, null, `Finding: ${trunc(m.claim, 40)} [${m.tier}]`); renderFindings(); spawnParticle('science', 'archive'); renderFeed(); },
      finding_validated: () => { addLog(m.timestamp, null, `Validated: ${trunc(m.claim, 40)}`); if (R.valVerdict) { R.valVerdict.textContent = 'STRONG'; R.valVerdict.setAttribute('fill', TIER_CLR.STRONG); setTimeout(() => R.valVerdict.textContent = '', 3000); } renderFeed(); },
      finding_rejected: () => { addLog(m.timestamp, null, `Rejected: ${trunc(m.claim, 40)}`); if (R.valVerdict) { R.valVerdict.textContent = 'NEGATIVE'; R.valVerdict.setAttribute('fill', TIER_CLR.NEGATIVE); setTimeout(() => R.valVerdict.textContent = '', 3000); } renderFeed(); },
      stage_transition: () => { state.current_stage = m.to_stage; for (const s of state.pipeline_state.stages) { if (s.name === m.from_stage) s.status = 'completed'; if (s.name === m.to_stage) s.status = 'active'; } addLog(m.timestamp, null, `Stage: ${m.from_stage} \u2192 ${m.to_stage}`); const dm = { acquire: 'command', analyze: 'science', validate: 'science', synthesize: 'archive', maintain: 'engine' }; if (dm[m.from_stage] && dm[m.to_stage] && dm[m.from_stage] !== dm[m.to_stage]) for (let i = 0; i < 3; i++) setTimeout(() => spawnParticle(dm[m.from_stage], dm[m.to_stage]), i * 150); renderCompass(); renderPipeline(); renderFeed(); },
      tool_health_update: () => { const idx = state.tool_health.findIndex(t => t.tool_id === m.tool_id); const t = { tool_id: m.tool_id, name: m.tool_id, uptime_pct: m.uptime_pct, status: m.status }; idx >= 0 ? state.tool_health[idx] = t : state.tool_health.push(t); renderTools(); },
    };
    if (h[m.type]) h[m.type]();
  }

  function addLog(ts, aid, text) {
    state.activity_log.push({ timestamp: ts || new Date().toISOString(), agent_id: aid, text });
    if (state.activity_log.length > 20) state.activity_log = state.activity_log.slice(-20);
  }

  // Interactions
  function setupInteractions() {
    rootEl.addEventListener('mousemove', onMove);
    rootEl.addEventListener('mouseleave', () => { const t = byId('vessel-tooltip'); if (t) t.classList.remove('vessel-tooltip--visible'); });
    rootEl.addEventListener('click', onClick);
  }

  function onMove(e) {
    const tgt = e.target.closest('.vessel-interactive, .vessel-finding-square, .vessel-health-bar-fill');
    const tip = byId('vessel-tooltip');
    if (!tgt || !tip) { if (tip) tip.classList.remove('vessel-tooltip--visible'); return; }
    let html = '';
    if (tgt.closest('[data-agent-id]')) {
      const aid = tgt.closest('[data-agent-id]').getAttribute('data-agent-id');
      const ar = tgt.closest('[data-agent-id]').getAttribute('data-agent-role');
      const a = state.active_agents.find(a => a.agent_id === aid);
      html = `<strong>${ar || aid}</strong><br>Stage: ${a ? a.stage : '\u2014'}<br>Status: ${a ? a.status : '\u2014'}`;
    } else if (tgt.closest('#station-orb')) {
      html = `Orchestrator: <strong>${state.orchestrator_status}</strong>`;
    } else if (tgt.closest('#station-compass')) {
      html = `Priority: <strong>${state.current_stage || 'none'}</strong>`;
    } else if (tgt.classList.contains('vessel-finding-square')) {
      const tier = tgt.getAttribute('data-tier');
      html = `Finding <span class="vessel-tooltip-tier vessel-tooltip-tier--${tier}">${tier}</span>`;
    } else if (tgt.classList.contains('vessel-health-bar-fill')) {
      const t = state.tool_health.find(t => t.tool_id === tgt.getAttribute('data-tool'));
      if (t) html = `<strong>${t.name}</strong><br>Uptime: ${t.uptime_pct}%<br>Status: ${t.status}`;
    } else if (tgt.closest('#station-tile')) {
      const t = state.current_tile;
      html = t ? `Tile: <strong>${t.tile_id}</strong><br>Cloud: ${t.cloud_cover}%<br>Status: ${t.status}` : 'No tile selected';
    }
    if (html) {
      tip.innerHTML = html;
      tip.classList.add('vessel-tooltip--visible');
      const r = rootEl.getBoundingClientRect();
      let x = e.clientX - r.left + 12, y = e.clientY - r.top - 8;
      if (x + 240 > r.width) x = e.clientX - r.left - 250;
      if (y < 0) y = 4;
      tip.style.left = x + 'px'; tip.style.top = y + 'px';
    } else tip.classList.remove('vessel-tooltip--visible');
  }

  function onClick(e) {
    if (e.target.closest('#station-shelves')) {
      try { if (window.parent !== window) window.parent.location.href = window.parent.location.origin + '/findings/'; } catch (err) {}
      return;
    }
    const se = e.target.closest('[data-agent-id]');
    if (se) { showPanel(se.getAttribute('data-agent-id')); return; }
    const p = byId('vessel-info-panel');
    if (p && !e.target.closest('.vessel-info-panel')) p.classList.remove('vessel-info-panel--visible');
  }

  function showPanel(aid) {
    const p = byId('vessel-info-panel');
    if (!p) return;
    const entries = state.activity_log.filter(e => e.agent_id === aid).slice(-3);
    if (!entries.length) { p.classList.remove('vessel-info-panel--visible'); return; }
    p.innerHTML = `<button class="vessel-info-panel-close" onclick="this.parentElement.classList.remove('vessel-info-panel--visible')">&times;</button>` +
      entries.map(e => `<div class="vessel-info-panel-entry">${new Date(e.timestamp).toLocaleTimeString('en-US', { hour12: false })} \u2014 ${escH(e.text)}</div>`).join('');
    p.classList.add('vessel-info-panel--visible');
  }

  // Responsive
  function checkResp() {
    const w = rootEl.offsetWidth;
    const m = w > 900 ? 'full' : w > 600 ? 'medium' : 'compact';
    if (m === rMode) return;
    rMode = m;
    const tabs = byId('vessel-deck-tabs'), tile = byId('station-tile');
    if (m === 'full') { if (tabs) tabs.classList.add('vessel-deck-tabs--hidden'); showDecks(); if (tile) tile.style.display = ''; }
    else if (m === 'medium') { if (tabs) tabs.classList.add('vessel-deck-tabs--hidden'); showDecks(); if (tile) tile.style.display = 'none'; }
    else { if (tabs) tabs.classList.remove('vessel-deck-tabs--hidden'); showDeck(activeDeckMobile); }
  }

  function showDecks() { for (const k of Object.keys(DECKS)) { const d = byId(`deck-${k}`); if (d) d.style.display = ''; } }
  function showDeck(k) { for (const dk of Object.keys(DECKS)) { const d = byId(`deck-${dk}`); if (d) d.style.display = dk === k ? '' : 'none'; } }

  function setupTabs() {
    const tabs = byId('vessel-deck-tabs');
    if (!tabs) return;
    tabs.addEventListener('click', e => {
      const t = e.target.closest('.vessel-deck-tab');
      if (!t) return;
      activeDeckMobile = t.getAttribute('data-deck');
      tabs.querySelectorAll('.vessel-deck-tab').forEach(b => b.classList.remove('vessel-deck-tab--active'));
      t.classList.add('vessel-deck-tab--active');
      showDeck(activeDeckMobile);
    });
  }

  // Mock data
  function loadMock() {
    Object.assign(state, {
      orchestrator_status: 'active', current_stage: 'analyze',
      active_agents: [
        { agent_id: 'geologist', role: 'chief-geologist', stage: 'analyze', status: 'active', initials: 'CG' },
        { agent_id: 'analyst-1', role: 'data-analyst', stage: 'analyze', status: 'active', initials: 'DA' },
      ],
      pipeline_state: { stages: [
        { name: 'acquire', status: 'completed' }, { name: 'analyze', status: 'active' },
        { name: 'validate', status: 'pending' }, { name: 'synthesize', status: 'pending' }, { name: 'maintain', status: 'pending' },
      ]},
      findings_summary: { total: 14, by_tier: { STRONG: 4, PRELIMINARY: 7, NEGATIVE: 2, TECHNICAL: 1 },
        timeline: [{ date: '05-28', count: 2 }, { date: '05-29', count: 5 }, { date: '05-30', count: 8 }, { date: '05-31', count: 10 }, { date: '06-01', count: 12 }, { date: '06-02', count: 14 }] },
      tool_health: [
        { tool_id: 'stac_search', name: 'STAC Search', uptime_pct: 95, status: 'healthy' },
        { tool_id: 'spectral', name: 'Spectral', uptime_pct: 88, status: 'healthy' },
        { tool_id: 'classifier', name: 'RF Classifier', uptime_pct: 72, status: 'degraded' },
        { tool_id: 'validation', name: 'Cross-Ref', uptime_pct: 100, status: 'healthy' },
      ],
      current_tile: { tile_id: 'T32RNQ-2026-05-15', bbox: [-4.2, 31.8, -3.5, 32.3], cloud_cover: 12, status: 'analyzing' },
      activity_log: [
        { timestamp: '2026-06-02T14:23:00Z', agent_id: 'cartographer', text: 'Acquired tile T32RNQ (cloud: 12%)' },
        { timestamp: '2026-06-02T14:25:00Z', agent_id: 'geologist', text: 'Iron oxide signature detected' },
        { timestamp: '2026-06-02T14:27:00Z', agent_id: 'analyst-1', text: 'RF classification: sandstone (0.87)' },
        { timestamp: '2026-06-02T14:29:00Z', text: 'Finding: Ferruginous sandstone [PRELIMINARY]' },
        { timestamp: '2026-06-02T14:30:00Z', agent_id: 'geologist', text: 'Cross-referencing Kem Kem outcrops' },
      ],
    });
  }

  function mockDemo() {
    const evts = [
      [2000, () => handleMsg({ type: 'stage_transition', timestamp: new Date().toISOString(), from_stage: 'analyze', to_stage: 'validate' })],
      [4000, () => handleMsg({ type: 'agent_start', timestamp: new Date().toISOString(), agent_id: 'validator', agent_role: 'validation-officer', stage: 'validate', detail: 'Validating ferruginous sandstone' })],
      [6000, () => handleMsg({ type: 'finding_validated', timestamp: new Date().toISOString(), finding_id: 'f-015', claim: 'Ferruginous sandstone at 31.95N', tier: 'STRONG' })],
      [8000, () => handleMsg({ type: 'finding_new', timestamp: new Date().toISOString(), finding_id: 'f-016', claim: 'Carbonate nodule cluster', tier: 'PRELIMINARY' })],
      [10000, () => handleMsg({ type: 'agent_complete', timestamp: new Date().toISOString(), agent_id: 'validator', agent_role: 'validation-officer', stage: 'validate', detail: '1 STRONG, 1 PRELIMINARY' })],
    ];
    evts.forEach(([d, fn]) => setTimeout(fn, d));
  }

  // Static idle data (vessel structure visible, no live data)
  function loadIdle() {
    Object.assign(state, {
      orchestrator_status: 'idle', current_stage: null,
      active_agents: [],
      pipeline_state: { stages: ['acquire','analyze','validate','synthesize','maintain'].map(n => ({ name: n, status: 'pending' })) },
      findings_summary: { total: 0, by_tier: { STRONG: 0, PRELIMINARY: 0, NEGATIVE: 0, TECHNICAL: 0 }, timeline: [] },
      tool_health: [
        { tool_id: 'stac_search', name: 'STAC Search', uptime_pct: 100, status: 'healthy' },
        { tool_id: 'spectral', name: 'Spectral', uptime_pct: 100, status: 'healthy' },
        { tool_id: 'classifier', name: 'RF Classifier', uptime_pct: 100, status: 'healthy' },
        { tool_id: 'validation', name: 'Cross-Ref', uptime_pct: 100, status: 'healthy' },
      ],
      current_tile: null,
      activity_log: [
        { timestamp: new Date().toISOString(), text: 'Awaiting first expedition run' },
      ],
    });
  }

  // Init
  function init() {
    rootEl = byId('vessel-root');
    if (!rootEl) return;
    svgEl = createSVG();
    rootEl.insertBefore(svgEl, rootEl.firstChild);
    const p = new URLSearchParams(window.location.search);
    if (p.get('demo') === 'true') { loadMock(); render(); mockDemo(); }
    else if (p.get('ws')) { loadIdle(); render(); wsConnect(); }
    else { loadIdle(); render(); }
    setupInteractions();
    setupTabs();
    checkResp();
    window.addEventListener('resize', checkResp);
    staleTimer = setInterval(() => { if (lastEvt && (Date.now() - lastEvt) > 300000) renderFeed(); }, 60000);
  }

  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', init) : init();
})();
