/**
 * NSE Findings Page — findings.js
 * Letter-sharded search index + MD5-keyed detail loading.
 * Same pattern as 30 quest board tools.
 */

(function () {
  'use strict';

  const INDEX_BASE = 'data/';
  const DETAIL_BASE = 'detail/';

  let currentIndex = null;   // Loaded shard
  let currentLetter = null;  // Which shard is loaded
  let activeFilter = 'all';

  const searchInput = document.getElementById('finding-search');
  const resultCount = document.getElementById('result-count');
  const findingsGrid = document.getElementById('findings-grid');
  const filterBtns = document.querySelectorAll('.filter-btn');

  // --- Shard Loading ---

  async function loadIndexShard(letter) {
    if (letter === currentLetter && currentIndex) return currentIndex;
    const key = letter.match(/^[a-z]$/) ? letter : '_';
    try {
      const resp = await fetch(`${INDEX_BASE}index_${key}.json`);
      if (!resp.ok) return [];
      currentIndex = await resp.json();
      currentLetter = key;
      return currentIndex;
    } catch (e) {
      return [];
    }
  }

  async function loadDetail(findingId) {
    const shardKey = md5Prefix(findingId);
    try {
      const resp = await fetch(`${DETAIL_BASE}${shardKey}.json`);
      if (!resp.ok) return null;
      const shard = await resp.json();
      return shard.find(f => f.id === findingId) || null;
    } catch (e) {
      return null;
    }
  }

  function md5Prefix(s) {
    // Simple hash for shard routing — same as Python hashlib.md5().hexdigest()[:2]
    // For client-side, we use a basic hash that maps to 00-ff
    let h = 0;
    for (let i = 0; i < s.length; i++) {
      h = ((h << 5) - h + s.charCodeAt(i)) | 0;
    }
    const hex = Math.abs(h).toString(16).padStart(4, '0');
    return hex.substring(0, 2);
  }

  // --- Search ---

  async function doSearch(query) {
    query = query.trim().toLowerCase();
    if (!query) {
      showEmpty('Enter a search term to find findings.');
      return;
    }

    const firstChar = query[0];
    const index = await loadIndexShard(firstChar);
    if (!index || index.length === 0) {
      showEmpty(`No findings starting with "${firstChar}".`);
      return;
    }

    let results = index.filter(f =>
      f.claim.toLowerCase().includes(query) ||
      (f.domain || '').toLowerCase().includes(query) ||
      (f.tile_id || '').toLowerCase().includes(query)
    );

    // Apply tier filter
    if (activeFilter !== 'all') {
      results = results.filter(f => (f.tier || 'preliminary').toLowerCase() === activeFilter);
    }

    if (results.length === 0) {
      showEmpty(`No findings match "${query}"${activeFilter !== 'all' ? ` (${activeFilter})` : ''}.`);
      return;
    }

    resultCount.textContent = `${results.length} finding${results.length !== 1 ? 's' : ''} found`;
    renderFindings(results);
  }

  // --- Render ---

  function renderFindings(findings) {
    findingsGrid.innerHTML = findings.map(f => `
      <div class="card" data-id="${escAttr(f.id)}" style="cursor: pointer;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.4rem;">
          <h3>${escHtml(f.claim)}</h3>
          <span class="tier tier-${(f.tier || 'preliminary').toLowerCase()}">${f.tier || 'PRELIMINARY'}</span>
        </div>
        <p>${escHtml(f.method || '')} &mdash; Season ${f.season || 1}</p>
        <div class="card-meta">
          <span>${escHtml(f.date || '')}</span>
          <span>Confidence: ${(f.confidence * 100).toFixed(0)}%</span>
          ${f.tile_id ? `<span>${escHtml(f.tile_id)}</span>` : ''}
        </div>
      </div>
    `).join('');

    // Click handlers for detail view
    findingsGrid.querySelectorAll('.card[data-id]').forEach(card => {
      card.addEventListener('click', () => showDetail(card.dataset.id));
    });
  }

  async function showDetail(findingId) {
    const detail = await loadDetail(findingId);
    if (!detail) return;

    const detailDiv = document.getElementById('finding-detail');
    const content = document.getElementById('detail-content');
    if (!detailDiv || !content) return;

    content.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
        <h3>${escHtml(detail.claim)}</h3>
        <span class="tier tier-${(detail.validation?.status || 'preliminary').toLowerCase()}">
          ${detail.validation?.status || 'PRELIMINARY'}
        </span>
      </div>
      <p>${escHtml(detail.method || '')}</p>
      <table class="mt-1" style="font-size: 0.82rem;">
        <tr><td class="dim" style="width: 140px;">Date</td><td>${escHtml(detail.date || '')}</td></tr>
        <tr><td class="dim">Domain</td><td>${escHtml(detail.domain || '')}</td></tr>
        <tr><td class="dim">Season</td><td>${detail.season || 1}</td></tr>
        <tr><td class="dim">Confidence</td><td>${(detail.confidence * 100).toFixed(1)}%</td></tr>
        <tr><td class="dim">Tool Version</td><td><code>${escHtml(detail.tool_version || '')}</code></td></tr>
        ${detail.location ? `<tr><td class="dim">Location</td><td>${escHtml(JSON.stringify(detail.location))}</td></tr>` : ''}
        ${detail.validation?.method ? `<tr><td class="dim">Validation</td><td>${escHtml(detail.validation.method)} (${escHtml(detail.validation.metric || '')})</td></tr>` : ''}
      </table>
      ${detail.retrieval_hints ? `
        <div class="mt-1">
          <span class="dim" style="font-size: 0.75rem;">Retrieval hints:</span>
          ${detail.retrieval_hints.map(h => `<span class="mono dim" style="font-size: 0.75rem; margin-left: 0.5rem;">${escHtml(h)}</span>`).join('')}
        </div>
      ` : ''}
      <div class="mt-2">
        <button onclick="document.getElementById('finding-detail').classList.add('hidden')"
          style="padding: 0.4rem 1rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text-secondary); cursor: pointer;">
          Close
        </button>
      </div>
    `;

    detailDiv.classList.remove('hidden');
    detailDiv.scrollIntoView({ behavior: 'smooth' });
  }

  function showEmpty(msg) {
    resultCount.textContent = '';
    findingsGrid.innerHTML = `
      <div class="card">
        <p class="dim text-center" style="padding: 2rem 0;">${escHtml(msg)}</p>
      </div>
    `;
  }

  // --- Utils ---

  function escHtml(s) {
    const d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
  }

  function escAttr(s) {
    return String(s).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // --- Init ---

  let searchTimeout;
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => doSearch(searchInput.value), 200);
    });
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = btn.dataset.tier;
      if (searchInput && searchInput.value.trim()) {
        doSearch(searchInput.value);
      }
    });
  });
})();
