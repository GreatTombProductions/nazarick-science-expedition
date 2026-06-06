/**
 * NSE Golem Chat Widget
 *
 * FILE_TRAJECTORY: load-bearing
 * TRAJECTORY_NOTE: NSE Ops Season 1 WS2. Vanilla JS chat panel for the crew page.
 *   Talks to the FastAPI chat server (chat/server.py) on the same host.
 *   No framework dependencies. Session-local conversation history.
 */

(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // Config
  // ---------------------------------------------------------------------------

  // Chat server URL — self-hosted on saturna. In production the site is on
  // GitHub Pages, so this points at the actual server. For local dev, override
  // via data-chat-url on the script tag.
  // Resolve chat server URL:
  //  1. data-chat-url on <script> tag (local dev override)
  //  2. Same host on port 8901 (self-hosted saturna)
  var scriptTag = document.currentScript;
  var CHAT_API = (scriptTag && scriptTag.dataset.chatUrl)
    || window.location.protocol + '//' + window.location.hostname + ':8901';

  const MAX_INPUT_LENGTH = 2000;

  // Golem emoji mapping (matches crew page avatars)
  const GOLEM_EMOJI = {
    'expedition-commander': '\u2694',
    'chief-geologist': '\uD83D\uDC8E',
    'data-analyst': '\uD83D\uDCCA',
    'validation-officer': '\u2696',
    'pipeline-engineer': '\u2699',
    'cartographer': '\uD83D\uDDFA',
    'ships-engineer': '\uD83D\uDD27',
    'field-surveyor': '\uD83D\uDD0D',
    'research-librarian': '\uD83D\uDCDA',
    'pandoras-actor': '\uD83C\uDFAD',
    'navigator': '\uD83D\uDCCF',
    'lookout': '\uD83D\uDD2E',
  };

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------

  let currentGolem = null;     // { id, name, role }
  let messages = [];           // [{ role: 'user'|'assistant', content }]
  let sessionId = null;
  let isLoading = false;
  let serverAvailable = null;  // null = unknown, true/false after check

  // DOM references (set in init)
  let panel, overlay, messagesEl, inputEl, sendBtn, headerAvatar,
      headerName, headerRole, typingEl, unavailableEl, inputArea;

  // ---------------------------------------------------------------------------
  // Session ID
  // ---------------------------------------------------------------------------

  function getSessionId() {
    if (!sessionId) {
      sessionId = 'sess_' + Date.now().toString(36) + '_' +
                  Math.random().toString(36).slice(2, 8);
    }
    return sessionId;
  }

  // ---------------------------------------------------------------------------
  // Server health check
  // ---------------------------------------------------------------------------

  async function checkServer() {
    try {
      const resp = await fetch(CHAT_API + '/health', {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      serverAvailable = resp.ok;
    } catch {
      serverAvailable = false;
    }
    return serverAvailable;
  }

  // ---------------------------------------------------------------------------
  // DOM creation
  // ---------------------------------------------------------------------------

  function createWidget() {
    // Overlay
    overlay = document.createElement('div');
    overlay.className = 'chat-overlay';
    overlay.addEventListener('click', closeChat);

    // Panel
    panel = document.createElement('div');
    panel.className = 'chat-panel';
    panel.innerHTML = `
      <div class="chat-header">
        <div class="chat-header-avatar" id="chat-avatar"></div>
        <div class="chat-header-info">
          <div class="chat-header-name" id="chat-name"></div>
          <div class="chat-header-role" id="chat-role"></div>
        </div>
        <button class="chat-close-btn" aria-label="Close chat">&times;</button>
      </div>
      <div class="chat-unavailable" id="chat-unavailable" style="display:none">
        <div class="chat-unavailable-icon">&middot;&middot;&middot;</div>
        <div>Chat server is offline.</div>
        <div style="font-size:0.75rem">The golems are busy with expedition work. Try again later.</div>
      </div>
      <div class="chat-messages" id="chat-messages"></div>
      <div class="chat-input-area" id="chat-input-area">
        <div class="chat-input-row">
          <textarea class="chat-input" id="chat-input"
                    placeholder="Ask about the expedition..."
                    rows="1" maxlength="${MAX_INPUT_LENGTH}"></textarea>
          <button class="chat-send-btn" id="chat-send" aria-label="Send" disabled>&#x27A4;</button>
        </div>
        <div class="chat-footer-info">
          Powered by Gemma 4 via OpenRouter &mdash; avatars only, no expedition access
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(panel);

    // Grab references
    headerAvatar = panel.querySelector('#chat-avatar');
    headerName = panel.querySelector('#chat-name');
    headerRole = panel.querySelector('#chat-role');
    messagesEl = panel.querySelector('#chat-messages');
    inputEl = panel.querySelector('#chat-input');
    sendBtn = panel.querySelector('#chat-send');
    unavailableEl = panel.querySelector('#chat-unavailable');
    inputArea = panel.querySelector('#chat-input-area');

    // Close button
    panel.querySelector('.chat-close-btn').addEventListener('click', closeChat);

    // Send handlers
    sendBtn.addEventListener('click', sendMessage);
    inputEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Auto-resize textarea
    inputEl.addEventListener('input', function () {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 120) + 'px';
      sendBtn.disabled = !this.value.trim() || isLoading;
    });
  }

  // ---------------------------------------------------------------------------
  // Chat buttons on crew cards
  // ---------------------------------------------------------------------------

  function addChatButtons() {
    // Golem ID mapping from card content — match by name
    const nameToId = {};
    const golems = document.querySelectorAll('#crew-grid .card');

    // Build name→ID map from GOLEM_EMOJI keys and card <h3> text
    const idToName = {
      'expedition-commander': 'Demiurge',
      'chief-geologist': 'Aura',
      'data-analyst': 'Mare',
      'validation-officer': 'Neuronist',
      'pipeline-engineer': 'Cocytus',
      'cartographer': 'Yuri',
      'ships-engineer': 'Rubedo',
      'field-surveyor': 'Nigredo',
      'research-librarian': 'Titus',
      'pandoras-actor': "Pandora's Actor",
      'navigator': 'Renner',
      'lookout': 'Pulcinella',
    };

    // Reverse: name → id
    for (var id in idToName) {
      nameToId[idToName[id]] = id;
    }

    // Role mapping
    const idToRole = {
      'expedition-commander': 'Expedition Commander',
      'chief-geologist': 'Chief Geologist',
      'data-analyst': 'Data Analyst',
      'validation-officer': 'Validation Officer',
      'pipeline-engineer': 'Pipeline Engineer',
      'cartographer': 'Cartographer',
      'ships-engineer': "Ship's Engineer",
      'field-surveyor': 'Field Surveyor',
      'research-librarian': 'Research Librarian',
      'pandoras-actor': "Pandora's Actor",
      'navigator': 'Navigator',
      'lookout': 'Lookout',
    };

    golems.forEach(function (card) {
      var h3 = card.querySelector('h3');
      if (!h3) return;
      var name = h3.textContent.trim();
      var golemId = nameToId[name];
      if (!golemId) return;

      var btn = document.createElement('button');
      btn.className = 'crew-chat-btn';
      btn.innerHTML = '<span class="chat-icon">&#x1F4AC;</span> Chat';
      btn.dataset.golemId = golemId;
      btn.dataset.golemName = name;
      btn.dataset.golemRole = idToRole[golemId] || '';

      btn.addEventListener('click', function () {
        openChat({
          id: this.dataset.golemId,
          name: this.dataset.golemName,
          role: this.dataset.golemRole,
        });
      });

      // Append after the <p> description
      var info = card.querySelector('.crew-info');
      if (info) info.appendChild(btn);
    });
  }

  // ---------------------------------------------------------------------------
  // Open / Close
  // ---------------------------------------------------------------------------

  function openChat(golem) {
    // If switching golems, reset conversation
    if (!currentGolem || currentGolem.id !== golem.id) {
      currentGolem = golem;
      messages = [];
      sessionId = null;
      renderMessages();
    }

    // Update header
    headerAvatar.textContent = GOLEM_EMOJI[golem.id] || '?';
    headerName.textContent = golem.name;
    headerRole.textContent = golem.role;

    // Show panel
    panel.classList.add('open');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';

    // Check server availability
    checkServer().then(function (available) {
      if (available) {
        unavailableEl.style.display = 'none';
        messagesEl.style.display = 'flex';
        inputArea.style.display = 'block';

        // Welcome message if empty conversation
        if (messages.length === 0) {
          appendSystemMessage(
            'You\'re chatting with ' + golem.name + ', ' + golem.role +
            ' aboard R/V Agnostophage. This is a read-only avatar \u2014 ' +
            'it shares the golem\'s knowledge but can\'t take expedition actions.'
          );
        }

        inputEl.focus();
      } else {
        unavailableEl.style.display = 'flex';
        messagesEl.style.display = 'none';
        inputArea.style.display = 'none';
      }
    });
  }

  function closeChat() {
    panel.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  // ---------------------------------------------------------------------------
  // Message rendering
  // ---------------------------------------------------------------------------

  function renderMessages() {
    messagesEl.innerHTML = '';
  }

  function appendMessage(role, content) {
    var div = document.createElement('div');
    if (role === 'system') {
      div.className = 'chat-msg chat-msg-system';
    } else if (role === 'user') {
      div.className = 'chat-msg chat-msg-user';
    } else {
      div.className = 'chat-msg chat-msg-assistant';
    }
    div.textContent = content;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function appendSystemMessage(text) {
    appendMessage('system', text);
  }

  function appendError(text) {
    var div = document.createElement('div');
    div.className = 'chat-error';
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function showTyping() {
    typingEl = document.createElement('div');
    typingEl.className = 'chat-typing';
    typingEl.id = 'chat-typing';
    typingEl.innerHTML =
      '<div class="chat-typing-dot"></div>' +
      '<div class="chat-typing-dot"></div>' +
      '<div class="chat-typing-dot"></div>';
    messagesEl.appendChild(typingEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function hideTyping() {
    var el = document.getElementById('chat-typing');
    if (el) el.remove();
    typingEl = null;
  }

  // ---------------------------------------------------------------------------
  // Send message
  // ---------------------------------------------------------------------------

  async function sendMessage() {
    var text = inputEl.value.trim();
    if (!text || isLoading || !currentGolem) return;

    // Add user message
    messages.push({ role: 'user', content: text });
    appendMessage('user', text);

    // Clear input
    inputEl.value = '';
    inputEl.style.height = 'auto';
    sendBtn.disabled = true;
    isLoading = true;
    showTyping();

    try {
      var resp = await fetch(CHAT_API + '/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          golem: currentGolem.id,
          messages: messages,
          session_id: getSessionId(),
        }),
      });

      hideTyping();

      if (!resp.ok) {
        var err;
        try {
          err = await resp.json();
        } catch {
          err = { detail: 'Server error (' + resp.status + ')' };
        }
        appendError(err.detail || 'Something went wrong. Try again.');
        // Remove the user message from history so it can be retried
        messages.pop();
        return;
      }

      var data = await resp.json();
      messages.push({ role: 'assistant', content: data.response });
      appendMessage('assistant', data.response);

    } catch (e) {
      hideTyping();
      appendError('Could not reach the chat server. Is it running?');
      messages.pop();
    } finally {
      isLoading = false;
      sendBtn.disabled = !inputEl.value.trim();
    }
  }

  // ---------------------------------------------------------------------------
  // Keyboard: Escape to close
  // ---------------------------------------------------------------------------

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && panel && panel.classList.contains('open')) {
      closeChat();
    }
  });

  // ---------------------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------------------

  function init() {
    createWidget();
    addChatButtons();
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
