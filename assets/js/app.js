/**
 * NSE Landing Page — app.js
 * Loads stats from findings manifest and renders latest findings.
 */

(function () {
  'use strict';

  const MANIFEST_URL = 'findings/data/findings-manifest.json';

  async function loadStats() {
    try {
      const resp = await fetch(MANIFEST_URL);
      if (!resp.ok) return; // No manifest yet — leave defaults
      const manifest = await resp.json();

      const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
      };

      set('stat-findings', manifest.total || 0);
      set('stat-tiles', manifest.tiles_surveyed || 0);
      set('stat-validated', manifest.validated || 0);
    } catch (e) {
      // Manifest not yet generated — leave placeholder values
    }
  }

  async function loadLatestFindings() {
    try {
      const resp = await fetch(MANIFEST_URL);
      if (!resp.ok) return;
      const manifest = await resp.json();
      if (!manifest.latest || manifest.latest.length === 0) return;

      const grid = document.getElementById('latest-findings');
      if (!grid) return;

      grid.innerHTML = manifest.latest.map(f => `
        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.4rem;">
            <h3>${escHtml(f.claim)}</h3>
            <span class="tier tier-${(f.tier || 'preliminary').toLowerCase()}">${f.tier || 'PRELIMINARY'}</span>
          </div>
          <p>${escHtml(f.method || '')} &mdash; ${escHtml(f.date || '')}</p>
          <div class="card-meta">
            <span>Confidence: ${(f.confidence * 100).toFixed(0)}%</span>
            ${f.tile_id ? `<span>Tile: ${escHtml(f.tile_id)}</span>` : ''}
          </div>
        </div>
      `).join('');
    } catch (e) {
      // No findings yet
    }
  }

  function escHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  // Vessel iframe loader (Phase 2 — currently shows fallback)
  function initVessel() {
    // When the real-time layer is deployed, this will:
    // 1. Try loading the iframe src
    // 2. On success, show iframe, hide fallback
    // 3. On failure/timeout, show fallback message
    // For now, the fallback is always shown.
  }

  // Agent role → initials (matches activity.js)
  const AGENT_INITIALS = {
    'cartographer': 'CA', 'chief-geologist': 'CG', 'data-analyst': 'DA',
    'field-surveyor': 'FS', 'validation-officer': 'VO', 'research-librarian': 'RL',
    'pipeline-engineer': 'PE', 'pandoras-actor': 'PA', 'neuronist': 'NE',
    'aura': 'AU', 'mare': 'MA', 'victim': 'VI', 'orchestrator': 'SY',
  };

  async function loadFeedTeaser() {
    try {
      const resp = await fetch('activity/data/activity-teaser.json');
      if (!resp.ok) return;
      const events = await resp.json();
      if (!Array.isArray(events) || events.length === 0) return;

      const teaser = document.getElementById('feed-teaser');
      const empty = document.getElementById('feed-teaser-empty');
      const link = document.getElementById('feed-teaser-link');
      if (!teaser) return;

      if (empty) empty.style.display = 'none';
      if (link) link.style.display = '';

      const html = events.slice(0, 5).map(evt => {
        const agent = evt.agent || evt.from || 'unknown';
        const initials = AGENT_INITIALS[agent] || agent.substring(0, 2).toUpperCase();
        const title = escHtml(evt.title || '');
        const body = escHtml((evt.body || '').substring(0, 120));
        const ts = formatRelativeTime(evt.timestamp);

        return `
          <div class="feed-event">
            <div class="feed-event-avatar"><span>${initials}</span></div>
            <div class="feed-event-content">
              <div class="feed-event-header">
                <span class="feed-event-agent">${escHtml(agentName(agent))}</span>
                <span class="feed-event-time">${ts}</span>
              </div>
              <div class="feed-event-title">${title}</div>
              <div class="feed-event-body">${body}</div>
            </div>
          </div>`;
      }).join('');

      // Insert before the empty placeholder
      teaser.insertAdjacentHTML('beforeend', html);
    } catch (e) {
      // No feed data yet
    }
  }

  function agentName(role) {
    if (!role) return 'Unknown';
    return role.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  function formatRelativeTime(iso) {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      const diffMin = Math.floor((Date.now() - d) / 60000);
      if (diffMin < 1) return 'just now';
      if (diffMin < 60) return diffMin + 'm ago';
      if (diffMin < 1440) return Math.floor(diffMin / 60) + 'h ago';
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch (e) { return ''; }
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadLatestFindings();
    loadFeedTeaser();
    initVessel();
  });
})();
