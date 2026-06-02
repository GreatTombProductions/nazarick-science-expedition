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

  document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadLatestFindings();
    initVessel();
  });
})();
