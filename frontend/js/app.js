/**
 * DOOM AI - Main Client Application Coordinator
 * Handles WebSocket IPC, Web Speech API microphone integration,
 * UI state updates, and command dispatching.
 */

window.copyCodeSnippet = function(btn) {
  const wrapper = btn.closest('.code-block-wrapper');
  if (!wrapper) return;
  const codeEl = wrapper.querySelector('code');
  if (!codeEl) return;
  navigator.clipboard.writeText(codeEl.innerText).then(() => {
    const orig = btn.innerText;
    btn.innerText = '✓ Copied';
    btn.style.borderColor = '#00ff88';
    btn.style.color = '#ffffff';
    setTimeout(() => {
      btn.innerText = orig;
      btn.style.borderColor = '';
      btn.style.color = '';
    }, 1800);
  });
};

class VikramApp {
  constructor() {
    this.ws = null;
    this.speechRecognizer = null;
    this.isListening = false;
    this._httpFailures = 0;
    this._pingInterval = null;
    this._connWatchdog = null;
    this.transcriptHistory = [];
    this.inputCommandHistory = [];
    this.inputHistoryIndex = -1;
    this.commandCount = 0;
    this.isChatMuted = localStorage.getItem('doom_ai_chat_muted') === '1';
    this.fetchCommandCount();
    this.initWebSocket();
    this.startConnectionWatchdog();
    this.initSpeechRecognition();
    this.initUIEvents();
    this._loadTranscriptHistory();
  }

  async fetchCommandCount() {
    try {
      const res = await fetch('/api/history/count');
      if (res.ok) {
        const data = await res.json();
        if (data && typeof data.count === 'number') {
          this.updateCommandCount(data.count);
        }
      }
    } catch (e) {
      console.debug('Command count fetch notice:', e);
    }
  }

  updateCommandCount(count) {
    if (typeof count === 'number' && !isNaN(count)) {
      this.commandCount = count;
    }
    const badge = document.getElementById('transcript-count-badge');
    if (badge) {
      badge.innerText = `${this.commandCount} COMMAND${this.commandCount === 1 ? '' : 'S'}`;
    }
  }

  initWebSocket() {
    // If already open or connecting, do not duplicate
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    if (this.ws) {
      try {
        this.ws.onopen = null;
        this.ws.onmessage = null;
        this.ws.onclose = null;
        this.ws.onerror = null;
        this.ws.close();
      } catch (e) {}
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
      this.ws = new WebSocket(wsUrl);
    } catch (e) {
      console.warn('WebSocket creation failed, retrying in 1s:', e);
      setTimeout(() => this.initWebSocket(), 1000);
      return;
    }

    this.ws.onopen = () => {
      console.log('Connected directly to DOOM AI Background Service via WebSocket (Permanent Link).');
      this._httpFailures = 0;
      this.updateState('ONLINE');

      // Start 5-second WebSocket ping-pong heartbeat to guarantee link never drops
      if (this._pingInterval) clearInterval(this._pingInterval);
      this._pingInterval = setInterval(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          try {
            this.ws.send(JSON.stringify({ type: 'ping' }));
          } catch (e) {}
        }
      }, 5000);

      // Sync initial chat mute state
      if (this.isChatMuted && this.ws && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({
            type: 'set_chat_mute',
            data: { muted: true }
          }));
        } catch (e) {}
      }

      // Auto-start continuous microphone listening
      setTimeout(() => this.startListening(), 400);
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'pong') return; // Heartbeat acknowledged
        this.handleServerMessage(msg);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    this.ws.onclose = () => {
      if (this._pingInterval) clearInterval(this._pingInterval);
      console.warn('WebSocket link interrupted. Auto-reconnecting immediately...');
      this.checkHttpStatus();
      setTimeout(() => this.initWebSocket(), 600);
    };

    this.ws.onerror = (err) => {
      console.debug('WebSocket transient notice:', err);
      this.checkHttpStatus();
    };
  }

  startConnectionWatchdog() {
    // Keep-alive watchdog: periodically verifies WebSocket health
    if (this._connWatchdog) clearInterval(this._connWatchdog);
    this._connWatchdog = setInterval(() => {
      if (!this.ws || this.ws.readyState === WebSocket.CLOSED || this.ws.readyState === WebSocket.CLOSING) {
        this.initWebSocket();
      }
      this.checkHttpStatus();
    }, 2500);

    // Instant reconnect when laptop wakes from sleep or network reconnects
    window.addEventListener('online', () => {
      console.log('[DOOM Connection] Network reconnected. Re-establishing link...');
      this._notifiedOfflineMic = false;
      this.initWebSocket();
      this.checkHttpStatus();
    });

    window.addEventListener('offline', () => {
      console.log('[DOOM Connection] Wi-Fi disconnected. Native Windows offline voice engine active.');
      this.updateTranscript('DOOM', '"Wi-Fi disconnected. Native Windows offline voice engine is active on your laptop mic."');
      this.syncMicUI(true);
    });

    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
          this.initWebSocket();
        }
        this.checkHttpStatus();
      }
    });

    window.addEventListener('focus', () => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        this.initWebSocket();
      }
      this.checkHttpStatus();
    });
  }

  async checkHttpStatus() {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        this._httpFailures = 0;
        const data = await res.json();
        const activeState = (data.state && data.state !== 'OFFLINE') ? data.state : 'ONLINE';
        this.updateState(activeState);

        if (typeof data.command_count === 'number') {
          this.updateCommandCount(data.command_count);
        }

        // Also update telemetry if websocket is currently handshaking
        if ((!this.ws || this.ws.readyState !== WebSocket.OPEN) && window.diagnostics) {
          fetch('/api/telemetry').then(r => r.json()).then(t => window.diagnostics.updateUI(t)).catch(() => {});
        }

        if (!this.isListening) {
          this.startListening();
        }
      } else {
        this._httpFailures++;
        if (this._httpFailures >= 3) {
          this.updateState('OFFLINE');
        }
      }
    } catch (e) {
      this._httpFailures++;
      if (this._httpFailures >= 3) {
        this.updateState('OFFLINE');
      }
    }
  }

  handleServerMessage(msg) {
    const { type, data } = msg;

    if (type === 'init') {
      // Always hide setup wizard — device is auto-paired on startup
      if (window.setupWizard) {
        window.setupWizard.hide();
        const devIdEl = document.getElementById('hud-device-id');
        if (devIdEl && data.pairing) {
          devIdEl.innerText = `ID: ${data.pairing.device_id}`;
        }
      }

      if (data.state) this.updateState(data.state);
      if (typeof data.command_count === 'number') this.updateCommandCount(data.command_count);
      if (data.telemetry && window.diagnostics) {
        window.diagnostics.updateUI(data.telemetry);
      }
    } else if (type === 'state_change') {
      if (data.state) this.updateState(data.state);
      if (typeof data.command_count === 'number') this.updateCommandCount(data.command_count);
      if (data.command) {
        this.updateTranscript('MASTER', `"${data.command}"`);
      }
    } else if (type === 'command_count') {
      if (typeof data.count === 'number') this.updateCommandCount(data.count);
    } else if (type === 'tts_start') {
      this._isSpeaking = true;
      this._ttsEndTime = null;
      this.updateState('SPEAKING');
      this.updateTranscript('DOOM', `"${data.text}"`);
      if (window.visualizer) window.visualizer.setAudioLevel(0.85);
      // Abort active speech recognition during TTS to prevent audio loopback / echo
      if (this.speechRecognizer && this._isRecognizerActive) {
        try { this.speechRecognizer.abort(); } catch (e) {}
      }
    } else if (type === 'tts_end') {
      this._isSpeaking = false;
      this._ttsEndTime = Date.now();  // mark exact TTS end for echo gate
      this.updateState('ONLINE');
      if (window.visualizer) window.visualizer.setAudioLevel(0.0);
      // Resume recognition 300ms after assistant finishes speaking
      this.scheduleRestart(300);
    } else if (type === 'command_result') {
      const { raw_command, parsed, result } = data;
      if (typeof data.command_count === 'number') {
        this.updateCommandCount(data.command_count);
      }
      this.updateTranscript('DOOM', `"${result.voice_response || 'Okay.'}"`);

      // Update developer inspector if code command
      if (result.details && (result.details.language || result.details.compilation || result.details.execution)) {
        if (window.terminalManager) {
          window.terminalManager.updateDeveloperOutput(result.details);
        }
      }

      // Update AI Answer Displayer if question or knowledge answer
      if (result.details && result.details.answer) {
        this.showAiAnswerCard({
          query: result.details.query || raw_command,
          answer: result.details.answer,
          source_url: result.details.source_url || '',
          source_title: result.details.source_title || '',
          used_gemini: true,
          lang_name: result.details.lang || 'EN'
        });
      }

      // Add to history stream
      if (window.terminalManager) {
        window.terminalManager.appendHistoryItem({
          timestamp: new Date().toISOString(),
          raw_command: raw_command,
          intent: parsed.intent,
          doom_response: result.voice_response,
          vikram_response: result.voice_response
        });
      }
    } else if (type === 'telemetry' && window.diagnostics) {
      window.diagnostics.updateUI(data);
    } else if (type === 'battery_event') {
      this.updateTranscript('DOOM', `"${data.message}"`);
      if (data.percent !== undefined) {
        const batVal = document.getElementById('tele-battery-val');
        const batFill = document.getElementById('tele-battery-fill');
        const batSub = document.getElementById('tele-battery-sub');
        if (batVal) batVal.innerText = `${data.percent}%`;
        if (batFill) batFill.style.width = `${Math.min(100, data.percent)}%`;
        if (batSub) {
          if (data.event === 'full') batSub.innerText = 'Charge Full';
          else if (data.is_charging) batSub.innerText = 'Charging (AC)';
          else batSub.innerText = 'On Battery';
        }
      }
    } else if (type === 'wifi_event') {
      if (data && data.message) {
        this.updateTranscript('DOOM', `"${data.message}"`);
      }
    } else if (type === 'bluetooth_event') {
      if (data && data.message) {
        this.updateTranscript('DOOM', `"${data.message}"`);
      }
    } else if (type === 'doom_action') {
      // DOOM AI dramatic animation for radio toggles (WiFi / Bluetooth)
      if (data && data.type === 'radio_toggle') {
        this._playRadioToggleAnimation(data);
      }
    } else if (type === 'chat_stream_start') {
      this._switchToDevTab();
      const questionLine = document.getElementById('ai-question-line');
      const answerBody = document.getElementById('ai-answer-body');
      const langBadge = document.getElementById('ai-lang-badge');
      const displayer = document.getElementById('ai-answer-displayer');
      const searchState = document.getElementById('ai-searching-state');

      if (displayer) displayer.classList.add('has-answer');
      if (searchState) searchState.classList.add('hidden');
      if (questionLine) questionLine.innerText = data.query || 'Prompt';
      if (langBadge) langBadge.innerText = (data.lang_name || 'AI').toUpperCase();
      if (answerBody) {
        answerBody.innerHTML = '<span class="ai-stream-cursor">▌</span>';
      }
      this.updateTranscript('MASTER', `"${data.query}"`);
      this.updateState('PROCESSING');

    } else if (type === 'chat_stream_token') {
      const answerBody = document.getElementById('ai-answer-body');
      if (answerBody) {
        let cursor = answerBody.querySelector('.ai-stream-cursor');
        if (!cursor) {
          answerBody.innerHTML += '<span class="ai-stream-cursor">▌</span>';
          cursor = answerBody.querySelector('.ai-stream-cursor');
        }
        const textNode = document.createTextNode(data.token);
        answerBody.insertBefore(textNode, cursor);
        answerBody.scrollTop = answerBody.scrollHeight;
      }

    } else if (type === 'chat_stream_end') {
      const answerBody = document.getElementById('ai-answer-body');
      const searchState = document.getElementById('ai-searching-state');
      if (searchState) searchState.classList.add('hidden');

      if (answerBody) {
        if (data.full_text) {
          answerBody.innerHTML = this.renderMarkdown(data.full_text);
        } else {
          const cursor = answerBody.querySelector('.ai-stream-cursor');
          if (cursor) cursor.remove();
        }
        answerBody.scrollTop = 0;
      }
      this.updateTranscript('DOOM', `"${data.tts_text || 'Completed, Master.'}"`);
      this.updateState('ONLINE');

      // Update grounding source
      const sourceBox = document.getElementById('ai-answer-source');
      const sourceLink = document.getElementById('ai-source-link');
      if (sourceBox && sourceLink) {
        if (data.source_url) {
          sourceBox.classList.remove('hidden');
          sourceLink.href = data.source_url;
          sourceLink.innerText = data.source_title || data.source_url;
        } else {
          sourceBox.classList.add('hidden');
        }
      }

      const langBadge = document.getElementById('ai-lang-badge');
      if (langBadge) {
        langBadge.innerText = data.lang_name ? data.lang_name.toUpperCase() : 'GOOGLE GROUNDED';
      }

      const terminal = document.getElementById('terminal-output');
      if (terminal) {
        const divider = '// ' + '─'.repeat(44);
        terminal.textContent += `\n${divider}\n// DOOM LLM RESPONSE\n${divider}\n// Q: "${data.query}"\n//\n` +
          (data.full_text || '').split('\n').map(l => `// ${l}`).join('\n') + `\n${divider}`;
        terminal.scrollTop = terminal.scrollHeight;
      }

    } else if (type === 'ai_searching') {
      // Show the dev tab and display the searching spinner
      this._switchToDevTab();
      this.showAiSearching(data.query, data.lang);
    } else if (type === 'ai_answer') {
      // Populate and show the answer card
      this._switchToDevTab();
      this.showAiAnswerCard(data);
    }
  }

  updateState(state) {
    const statusLabel = document.getElementById('status-label');
    const statusPip = document.getElementById('status-pip');
    const coreBadge = document.getElementById('core-state-text');

    const cleanState = (state || '').replace(/^(?:VIKRAM|DOOM)\s+/i, '').trim();
    if (statusLabel) statusLabel.innerText = `DOOM ${cleanState}`;
    if (coreBadge) coreBadge.innerText = `◉ ${cleanState} ◉`;

    if (statusPip) {
      statusPip.className = 'status-pip';
      if (cleanState === 'ONLINE' || cleanState === 'VOICE VERIFIED') {
        statusPip.classList.add('online');
      } else if (cleanState === 'OFFLINE' || cleanState === 'ERROR') {
        statusPip.classList.add('offline');
      } else {
        statusPip.classList.add('busy');
      }
    }

    if (window.visualizer) {
      window.visualizer.setState(cleanState);
    }

    // Sync speech recognition listening with DOOM AI activation state
    if (cleanState === 'PAUSED') {
      this.stopListening();
    } else if ((cleanState === 'ONLINE' || cleanState === 'LISTENING') && !this.isListening) {
      this.startListening();
    }
  }

  updateTranscript(speaker, text) {
    const spkEl = document.getElementById('transcript-speaker');
    const txtEl = document.getElementById('transcript-text');
    if (spkEl) spkEl.innerText = speaker;
    if (txtEl) txtEl.innerText = text;

    const cleanText = (text || '').trim();
    if (!cleanText) return;

    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];

    const entry = {
      speaker: speaker || 'DOOM',
      text: cleanText,
      time: timeStr
    };

    if (!Array.isArray(this.transcriptHistory)) {
      this.transcriptHistory = [];
    }

    // No limit on transcript history
    this.transcriptHistory.push(entry);

    try {
      localStorage.setItem('doom_transcript_history', JSON.stringify(this.transcriptHistory));
    } catch (e) {}

    const stream = document.getElementById('transcript-stream');
    if (stream) {
      this._appendTranscriptItem(entry, stream);
    }

    // Update count badge with exact commands count
    this.updateCommandCount();
  }

  _appendTranscriptItem(entry, stream) {
    const isMaster = /master|you/i.test(entry.speaker);
    const itemEl = document.createElement('div');
    itemEl.className = `transcript-item ${isMaster ? 'master-item' : 'doom-item'}`;

    const metaEl = document.createElement('div');
    metaEl.className = 'item-meta';

    const spkTag = document.createElement('span');
    spkTag.className = `item-speaker ${isMaster ? 'speaker-master' : 'speaker-doom'}`;
    spkTag.innerText = entry.speaker.toUpperCase();

    const timeTag = document.createElement('span');
    timeTag.className = 'item-time';
    timeTag.innerText = entry.time || '';

    metaEl.appendChild(spkTag);
    metaEl.appendChild(timeTag);

    const contentEl = document.createElement('div');
    contentEl.className = 'item-content';
    contentEl.innerText = entry.text;

    itemEl.appendChild(metaEl);
    itemEl.appendChild(contentEl);

    stream.appendChild(itemEl);
    stream.scrollTop = stream.scrollHeight;
  }

  _playRadioToggleAnimation(data) {
    // Determine colors based on radio type and new state
    const radio = (data.radio || 'wifi').toLowerCase();
    const newState = (data.new_state || 'on').toLowerCase();

    let pulseColor, glowColor, icon, label;
    if (radio === 'wifi') {
      icon = newState === 'on' ? '📶' : '📵';
      label = newState === 'on' ? 'WI-FI ON' : 'WI-FI OFF';
      pulseColor = newState === 'on' ? '#00ff88' : '#ff3355';
      glowColor  = newState === 'on' ? 'rgba(0,255,136,0.55)' : 'rgba(255,51,85,0.55)';
    } else {
      icon = newState === 'on' ? '🔵' : '⚫';
      label = newState === 'on' ? 'BLUETOOTH ON' : 'BLUETOOTH OFF';
      pulseColor = newState === 'on' ? '#2979ff' : '#607d8b';
      glowColor  = newState === 'on' ? 'rgba(41,121,255,0.55)' : 'rgba(96,125,139,0.45)';
    }

    // 1. Flash the visualizer orb with a dramatic color pulse
    const orb = document.querySelector('.core-orb') || document.querySelector('.visualizer-core') || document.querySelector('#hud-orb');
    if (orb) {
      const prevFilter = orb.style.filter;
      const prevBg = orb.style.background;
      orb.style.transition = 'filter 0.12s ease, background 0.12s ease';
      orb.style.filter = `drop-shadow(0 0 28px ${pulseColor}) brightness(1.6)`;
      orb.style.background = pulseColor;
      setTimeout(() => {
        orb.style.filter = `drop-shadow(0 0 14px ${glowColor}) brightness(1.2)`;
        orb.style.background = '';
        setTimeout(() => {
          orb.style.filter = prevFilter || '';
          orb.style.transition = '';
        }, 600);
      }, 320);
    }

    // 2. Flash a temporary floating badge overlay on the HUD
    const badge = document.createElement('div');
    badge.id = 'doom-radio-badge';
    badge.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%) scale(0.7);
      z-index: 99999;
      background: rgba(10, 14, 26, 0.92);
      border: 2px solid ${pulseColor};
      border-radius: 14px;
      padding: 18px 36px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      pointer-events: none;
      box-shadow: 0 0 40px ${glowColor}, inset 0 0 24px rgba(0,0,0,0.6);
      transition: transform 0.18s cubic-bezier(0.34,1.56,0.64,1), opacity 0.18s ease;
      opacity: 0;
      font-family: 'Orbitron', 'Courier New', monospace;
    `;
    badge.innerHTML = `
      <span style="font-size:2.2rem;line-height:1;">${icon}</span>
      <span style="color:${pulseColor};font-size:1.05rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;">${label}</span>
    `;
    document.body.appendChild(badge);
    // Animate in
    requestAnimationFrame(() => {
      badge.style.opacity = '1';
      badge.style.transform = 'translate(-50%, -50%) scale(1)';
    });
    // Animate out and remove
    setTimeout(() => {
      badge.style.opacity = '0';
      badge.style.transform = 'translate(-50%, -50%) scale(0.75)';
      setTimeout(() => { if (badge.parentNode) badge.parentNode.removeChild(badge); }, 320);
    }, 900);

    // 3. Update transcript
    this.updateTranscript('DOOM', `"${icon} ${label}"`);

    // 4. Drive visualizer pulse if available
    if (window.visualizer) {
      window.visualizer.setAudioLevel(0.9);
      setTimeout(() => window.visualizer.setAudioLevel(0.0), 500);
    }
  }

  _loadTranscriptHistory() {
    const stream = document.getElementById('transcript-stream');
    if (!stream) return;

    try {
      const saved = localStorage.getItem('doom_transcript_history');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          this.transcriptHistory = parsed;
          stream.innerHTML = '';
          this.transcriptHistory.forEach(entry => this._appendTranscriptItem(entry, stream));
          this.updateCommandCount();
          return;
        }
      }
    } catch (e) {}

    this.transcriptHistory = [{ speaker: 'DOOM', text: '"Hello Master"', time: 'LIVE' }];
    this.updateCommandCount();
  }

  _clearTranscriptHistory() {
    this.transcriptHistory = [];
    try {
      localStorage.removeItem('doom_transcript_history');
    } catch (e) {}
    const stream = document.getElementById('transcript-stream');
    if (stream) {
      stream.innerHTML = '<div class="transcript-item doom-item"><div class="item-meta"><span class="item-speaker speaker-doom">DOOM</span><span class="item-time">READY</span></div><div class="item-content">"At your service, Master. Give any command."</div></div>';
    }
    this.updateCommandCount();
  }

  _switchToDevTab() {
    // Activate Developer tab
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    const devBtn = document.getElementById('tab-btn-dev');
    const devContent = document.getElementById('tab-content-dev');
    if (devBtn) devBtn.classList.add('active');
    if (devContent) devContent.classList.add('active');
  }

  showAiSearching(query, langName) {
    this._switchToDevTab();
    const searchState = document.getElementById('ai-searching-state');
    const searchMsg = document.getElementById('ai-search-msg');
    const questionLine = document.getElementById('ai-question-line');
    const langBadge = document.getElementById('ai-lang-badge');
    const displayer = document.getElementById('ai-answer-displayer');

    if (searchState) searchState.classList.remove('hidden');
    if (searchMsg) searchMsg.innerText = `Thinking & searching: "${query}"...`;
    if (questionLine) questionLine.innerText = query;
    if (langBadge && langName) langBadge.innerText = langName.toUpperCase();
    if (displayer) displayer.classList.add('has-answer');

    // Also mirror to terminal output
    const terminal = document.getElementById('terminal-output');
    if (terminal) {
      const lang = langName ? ` [${langName.toUpperCase()}]` : '';
      terminal.textContent += `\n// [AI]${lang} Searching: "${query}"...`;
      terminal.scrollTop = terminal.scrollHeight;
    }
  }

  renderMarkdown(text) {
    if (!text) return '';

    // Extract code blocks first to protect them from formatting modifications
    const codeBlocks = [];
    let processed = text.replace(/```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const id = `__CODE_BLOCK_${codeBlocks.length}__`;
      codeBlocks.push({ lang: lang.trim() || 'code', code: code.trimEnd() });
      return id;
    });

    // Escape HTML special characters
    processed = processed
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Headings with file names (e.g. ### 1. FileName.java or ### Method Overriding)
    processed = processed.replace(/^###\s+(?:(\d+\.\s+[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)|(.*))$/gm, (m, file, title) => {
      const name = file || title || '';
      const icon = file ? '📄' : '✦';
      return `<div class="ai-file-header"><span class="ai-file-icon">${icon}</span><span class="ai-file-name">${name.trim()}</span></div>`;
    });

    // Subheadings (#### Title)
    processed = processed.replace(/^####\s+(.*)$/gm, '<h4 class="ai-md-h4">$1</h4>');

    // Horizontal rule (---)
    processed = processed.replace(/^---+$/gm, '<hr class="ai-divider" />');

    // Bold text (**text**)
    processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong class="ai-bold">$1</strong>');

    // Inline code (`code`)
    processed = processed.replace(/`([^`\n]+)`/g, '<code class="ai-inline-code">$1</code>');

    // Numbered list items (1. item or 1. **title:** desc)
    processed = processed.replace(/^[ \t]*(\d+)\.\s+(.*)$/gm, '<div class="ai-list-item"><span class="ai-num-bullet">$1.</span><span class="ai-list-text">$2</span></div>');

    // Bullet points (- item or * item)
    processed = processed.replace(/^[ \t]*[\-\*]\s+(.*)$/gm, '<div class="ai-list-item"><span class="ai-bullet">▸</span><span class="ai-list-text">$1</span></div>');

    // Restore Code Blocks into Gemini-Style Code Cards
    codeBlocks.forEach((cb, idx) => {
      const escapedCode = cb.code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
      const langUpper = cb.lang.toUpperCase();
      const codeHtml = `
<div class="code-block-wrapper">
  <div class="code-block-header">
    <span class="code-lang-badge">${langUpper}</span>
    <button class="code-copy-btn" onclick="window.copyCodeSnippet(this)">📋 Copy</button>
  </div>
  <pre class="code-pre"><code>${escapedCode}</code></pre>
</div>`;
      processed = processed.replace(`__CODE_BLOCK_${idx}__`, codeHtml);
    });

    // Spacer for double newlines
    processed = processed.replace(/\n\n+/g, '<div style="height: 8px;"></div>');
    processed = processed.replace(/\n/g, '<br>');

    return processed;
  }

  showAiAnswerCard(data) {
    this._switchToDevTab();
    const searchState = document.getElementById('ai-searching-state');
    const questionLine = document.getElementById('ai-question-line');
    const answerBody = document.getElementById('ai-answer-body');
    const langBadge = document.getElementById('ai-lang-badge');
    const sourceBox = document.getElementById('ai-answer-source');
    const sourceLink = document.getElementById('ai-source-link');
    const poweredBy = document.getElementById('ai-powered-by');
    const displayer = document.getElementById('ai-answer-displayer');

    if (searchState) searchState.classList.add('hidden');
    if (displayer) displayer.classList.add('has-answer');

    if (questionLine) questionLine.innerText = data.query || 'Question';
    if (answerBody) {
      answerBody.innerHTML = this.renderMarkdown(data.answer || 'No response generated.');
      answerBody.scrollTop = 0;
    }
    if (langBadge) langBadge.innerText = data.lang_name ? data.lang_name.toUpperCase() : 'GOOGLE GROUNDED';

    if (sourceBox && sourceLink) {
      if (data.source_url) {
        sourceBox.classList.remove('hidden');
        sourceLink.href = data.source_url;
        sourceLink.innerText = data.source_title || data.source_url;
      } else {
        sourceBox.classList.add('hidden');
      }
    }

    if (poweredBy) {
      poweredBy.innerText = '⚡ Powered by Doom AI & Live Web Grounding';
    }

    // Mirror formatted text into console
    const terminal = document.getElementById('terminal-output');
    if (terminal) {
      const lang = data.lang_name ? ` [${data.lang_name.toUpperCase()}]` : '';
      const divider = '// ' + '─'.repeat(44);
      const question = `// Q: "${data.query}"`;
      const answer = (data.answer || 'No answer found.')
        .split('\n')
        .map(line => `//   ${line}`)
        .join('\n');
      const source = data.source_url
        ? `// Source: ${data.source_title || data.source_url}\n//         ${data.source_url}`
        : '';
      const powered = data.used_gemini
        ? '// ⚡ Powered by Doom AI + DuckDuckGo'
        : '// 🔍 Powered by DuckDuckGo Search';

      terminal.textContent +=
        `\n${divider}\n// DOOM AI ANSWER${lang}\n${divider}\n${question}\n//\n${answer}` +
        (source ? `\n//\n${source}` : '') +
        `\n${powered}\n${divider}`;

      terminal.scrollTop = terminal.scrollHeight;
    }
  }

  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Web Speech API not supported — native background listener will handle voice input.');
      return;
    }

    this._restartTimer = null;
    this._watchdogInterval = null;
    this._isSpeaking = false;
    this._isRecognizerActive = false;
    this._isStarting = false;
    this._restartDelay = 180;   // ms — reset on success, grows on repeated errors
    this._errorCount = 0;
    this._fastCommandTimer = null;
    this._lastDispatchedText = null;
    this._lastDispatchedTime = 0;

    // Activate Far-Field 20-Meter Acoustic Pre-Amplifier & Hardware AGC
    this._initFarFieldAudioBooster();

    this.currentLangMode = localStorage.getItem('doom_lang_mode') || 'auto';
    this.speechRecognizer = new SpeechRecognition();
    this.speechRecognizer.continuous = true;
    this.speechRecognizer.interimResults = true;   // show live words while speaking
    // Bilingual Speech Recognition: te-IN for Telugu, en-IN for English/Tanglish
    this.speechRecognizer.lang = this.currentLangMode === 'te' ? 'te-IN' : 'en-IN';
    this.speechRecognizer.maxAlternatives = 5;      // Capture up to 5 hypotheses for acoustic tolerance


    this.speechRecognizer.onstart = () => {
      this._isRecognizerActive = true;
      this._isStarting = false;
      this._errorCount = 0;
      this._restartDelay = 180;
      this.syncMicUI(true);
    };

    this.speechRecognizer.onaudiostart = () => {
      this._isRecognizerActive = true;
    };

    this.speechRecognizer.onresult = (event) => {
      // Acoustic echo suppression: ignore audio captured during TTS
      if (this._isSpeaking) return;
      if (this._ttsEndTime && (Date.now() - this._ttsEndTime) < 500) return;

      const lastResult = event.results[event.results.length - 1];
      let transcriptText = (lastResult[0].transcript || '').trim();
      if (!transcriptText) return;

      // Far-Field Multi-Alternative Inspection:
      // When speaking from 10 to 20 meters away, check all 5 candidate hypotheses for recognized commands
      for (let i = 0; i < lastResult.length; i++) {
        const candidate = (lastResult[i].transcript || '').trim();
        if (candidate && this._isActionCommand(candidate)) {
          transcriptText = candidate;
          break;
        }
      }

      // Real-time interim detection: execute under 1 second without waiting for Chrome's 2s delay
      if (!lastResult.isFinal) {
        this.updateTranscript('YOU', `"${transcriptText}..."`);

        if (this._fastCommandTimer) {
          clearTimeout(this._fastCommandTimer);
          this._fastCommandTimer = null;
        }

        const isAction = this._isActionCommand(transcriptText);
        const debounceMs = isAction ? 260 : 1200;

        this._fastCommandTimer = setTimeout(() => {
          this._dispatchVoiceCommand(transcriptText);
        }, debounceMs);
        return;
      }

      // Browser emitted isFinal: clear pending timer and dispatch
      if (this._fastCommandTimer) {
        clearTimeout(this._fastCommandTimer);
        this._fastCommandTimer = null;
      }

      // If action not already picked from multi-alternative scan, pick highest confidence
      if (!this._isActionCommand(transcriptText)) {
        let bestConf = 0;
        for (let i = 0; i < lastResult.length; i++) {
          if (lastResult[i].confidence >= bestConf) {
            bestConf = lastResult[i].confidence;
            transcriptText = (lastResult[i].transcript || '').trim();
          }
        }
      }

      this._dispatchVoiceCommand(transcriptText);
    };

    this.speechRecognizer.onerror = (err) => {
      console.debug('Speech recognition notice:', err.error);
      this._isStarting = false;

      if (err.error === 'not-allowed' || err.error === 'service-not-allowed') {
        // Mic permission denied — stop trying
        this.stopListening();
        this.updateTranscript('DOOM', '"Microphone access denied. Please allow mic in browser."');
        return;
      }

      if (err.error === 'network') {
        // Web Speech API requires cloud connection.
        // When Wi-Fi is disconnected, Local faster-whisper STT handles laptop mic 100% offline.
        this._isOffline = true;
        if (!this._notifiedOfflineMic) {
          this._notifiedOfflineMic = true;
          this.updateTranscript('DOOM', '"Wi-Fi disconnected. Local Whisper offline voice recognition is active."');
          this.updateState('OFFLINE (VOICE ACTIVE)');
        }
        this.syncMicUI(true);
        // Do not hammer Chrome speech recognition while offline; wait for network restoration
        return;
      }

      // no-speech, aborted, audio-capture — these are normal; recover gracefully
      if (this.isListening && !this._isSpeaking && !this._isOffline) {
        this._scheduleRestartWithBackoff();
      }
    };

    this.speechRecognizer.onend = () => {
      this._isRecognizerActive = false;
      this._isStarting = false;
      // Auto-restart loop: guarantees the microphone re-arms continuously when online
      if (this.isListening && !this._isSpeaking && (!this._isOffline || navigator.onLine)) {
        this.scheduleRestart(this._restartDelay);
      }
    };

    // Auto-resume when user returns to the DOOM tab
    const handleReactivation = () => {
      if (!document.hidden && this.isListening && !this._isRecognizerActive && !this._isSpeaking && navigator.onLine) {
        this.safeStartRecognizer();
      }
    };
    document.addEventListener('visibilitychange', handleReactivation);
    window.addEventListener('focus', handleReactivation);

    // Online / Offline network recovery hooks
    window.addEventListener('online', () => {
      console.log('Network online detected: restoring Web Speech recognition.');
      this._isOffline = false;
      this._notifiedOfflineMic = false;
      this.updateState('ONLINE');
      this.updateTranscript('DOOM', '"Wi-Fi reconnected. Full online AI mode active."');
      if (this.isListening && !this._isSpeaking) {
        this.safeStartRecognizer();
      }
    });

    window.addEventListener('offline', () => {
      console.log('Network offline detected: switching mic to Local Whisper offline listener.');
      this._isOffline = true;
      if (this.speechRecognizer && this._isRecognizerActive) {
        try { this.speechRecognizer.abort(); } catch (e) {}
      }
      this.syncMicUI(true);
      if (!this._notifiedOfflineMic) {
        this._notifiedOfflineMic = true;
        this.updateTranscript('DOOM', '"Wi-Fi disconnected. Local Whisper offline voice recognition is active."');
      }
      this.updateState('OFFLINE (VOICE ACTIVE)');
    });

    // Watchdog: ensures the mic never permanently dies
    this.startWatchdog();
  }

  _isActionCommand(text) {
    let t = (text || '').toLowerCase().trim();
    if (!t) return false;

    // Strip leading distant wake acoustic aliases
    t = t.replace(/^(?:hey\s+doom|hi\s+doom|ok\s+doom|doom\s+ai|doom|vikram|bikram)\s*[,:\-]?\s*/i, '').trim();

    // Telugu Unicode script detection (\u0C00-\u0C7F)
    if (/[\u0C00-\u0C7F]/.test(t)) return true;

    // Tanglish action markers
    if (t.includes('cheyyi') || t.includes('chey') || t.includes('pettu') || t.includes('pampu') ||
        t.includes('penchu') || t.includes('thagginchu') || t.includes('tagginchu') ||
        t.includes('moosi') || t.includes('aapu') || t.includes('entha') || t.includes('enti') ||
        t.includes('samayam') || t.includes('namaskaram') || t.includes('namaste') ||
        t.includes('theruvu') || t.includes('lekkimchu')) return true;

    // Battery & charging telemetry
    if (t.includes('charg') || t.includes('chrag') || t.includes('battery') || t.includes('bettery') || t.includes('battry') || t.includes('percent') || t.includes('level')) return true;
    // Apps launch / close
    if (/^(?:open|launch|start|close|quit|exit|kill|stop)\s+/i.test(t)) return true;
    // Search & Google queries
    if (/^(?:search|google|find|lookup|look up)\b/i.test(t)) return true;
    // Hardware & system controls
    if (t.includes('wifi') || t.includes('wi-fi') || t.includes('bluetooth') || t.includes('volume') || t.includes('mute') || t.includes('unmute')) return true;
    if (t.includes('bright') || t.includes('brigth') || t.includes('airplane') || t.includes('aeroplane') || t.includes('areplane') || t.includes('magnif') || t.includes('narrat') || t.includes('keyboard') || t.includes('osk') || t.includes('setting') || t.includes('contrast')) return true;
    if (t.includes('lock') || t.includes('unlock') || t.includes('sleep') || t.includes('restart') || t.includes('shutdown') || t.includes('screenshot')) return true;
    // Clock & date
    if (t.includes('time') || t.includes('date')) return true;
    // Standalone quick keywords
    if (['battery', 'charging', 'chraging', 'charge', 'wifi', 'bluetooth', 'airplane', 'aeroplane', 'areplane', 'brightness', 'volume', 'lock', 'time', 'date', 'search', 'search that', 'google', 'hi', 'hello', 'hey doom', 'doom'].includes(t)) return true;
    return false;
  }


  _initFarFieldAudioBooster() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
    try {
      // 20-Meter Far-Field Audio Pre-Amplifier:
      // Engages hardware Auto-Gain Control (AGC), noise suppression, and dynamic range compression
      navigator.mediaDevices.getUserMedia({
        audio: {
          autoGainControl: true,       // Hardware AGC amplifies distant voices (up to 20m)
          noiseSuppression: true,      // Eliminates steady fan and AC noise
          echoCancellation: true,      // Cancels speaker reflections
          channelCount: 1,
          sampleRate: 48000
        }
      }).then(stream => {
        console.log('[DOOM Far-Field Audio] Hardware AGC & Noise Suppression active (20-Meter Range enabled).');
        this._audioStream = stream;
        try {
          const AudioCtx = window.AudioContext || window.webkitAudioContext;
          if (AudioCtx) {
            const ctx = new AudioCtx();
            const source = ctx.createMediaStreamSource(stream);

            // Dynamics Compressor boosts distant acoustic signals while preventing close clipping
            const compressor = ctx.createDynamicsCompressor();
            compressor.threshold.setValueAtTime(-45, ctx.currentTime);
            compressor.knee.setValueAtTime(30, ctx.currentTime);
            compressor.ratio.setValueAtTime(12, ctx.currentTime);
            compressor.attack.setValueAtTime(0.003, ctx.currentTime);
            compressor.release.setValueAtTime(0.25, ctx.currentTime);

            // Digital Gain Pre-Amplifier (+11dB gain)
            const gainNode = ctx.createGain();
            gainNode.gain.setValueAtTime(3.5, ctx.currentTime);

            source.connect(compressor);
            compressor.connect(gainNode);

            // Route to virtual destination without playback (prevents speaker echo loop)
            const dest = ctx.createMediaStreamDestination();
            gainNode.connect(dest);
            this._audioCtx = ctx;
          }
        } catch (e) {
          console.debug('WebAudio processing notice:', e);
        }
      }).catch(err => {
        console.debug('Far-Field AGC notice:', err);
      });
    } catch (e) {
      console.debug('Far-field audio initialization notice:', e);
    }
  }

  _dispatchVoiceCommand(text) {
    const cleanText = (text || '').trim();
    if (!cleanText) return;

    // Echo & loopback suppression
    if (this._isSpeaking) return;

    // Deduplicate against recent dispatch within 2200ms
    const now = Date.now();
    if (this._lastDispatchedText &&
        (cleanText.toLowerCase() === this._lastDispatchedText.toLowerCase() ||
         cleanText.toLowerCase().startsWith(this._lastDispatchedText.toLowerCase())) &&
        (now - this._lastDispatchedTime < 2200)) {
      return;
    }

    this._lastDispatchedText = cleanText;
    this._lastDispatchedTime = now;

    if (this._fastCommandTimer) {
      clearTimeout(this._fastCommandTimer);
      this._fastCommandTimer = null;
    }

    console.log(`[Fast-Voice-Dispatch <1s] "${cleanText}"`);
    this.updateTranscript('YOU', `"${cleanText}"`);
    this.commandCount++;
    this.updateCommandCount(this.commandCount);

    // Transmit instantly via WebSocket to backend ActionDispatcher
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'speech_input',
        data: { text: cleanText, audio_features: [0.35, 0.52, 0.48, 0.61, 0.72] }
      }));
    }
  }

  _scheduleRestartWithBackoff(baseDelay = 250) {
    this._errorCount = (this._errorCount || 0) + 1;
    // Exponential backoff capped at 3 seconds
    const delay = Math.min(baseDelay * Math.pow(1.5, Math.min(this._errorCount, 6)), 3000);
    this.scheduleRestart(delay);
  }

  safeStartRecognizer() {
    if (!this.isListening || this._isSpeaking || this._isRecognizerActive || this._isStarting) {
      return;
    }
    if (!this.speechRecognizer) return;

    this._isStarting = true;
    try {
      this.speechRecognizer.start();
    } catch (err) {
      this._isStarting = false;
      if (err.name === 'InvalidStateError') {
        // Recognition might already be running or in stopping transition
        if (err.message && err.message.toLowerCase().includes('already started')) {
          this._isRecognizerActive = true;
        } else {
          this.scheduleRestart(350);
        }
      } else {
        this.scheduleRestart(500);
      }
    }
  }

  scheduleRestart(delay = 200) {
    if (!this.isListening || this._isSpeaking) return;
    clearTimeout(this._restartTimer);
    this._restartTimer = setTimeout(() => {
      this.safeStartRecognizer();
    }, delay);
  }

  startWatchdog() {
    if (this._watchdogInterval) clearInterval(this._watchdogInterval);
    this._watchdogInterval = setInterval(() => {
      if (this.isListening && !this._isRecognizerActive && !this._isSpeaking && !this._isStarting) {
        this.safeStartRecognizer();
      }
    }, 1200);
  }

  syncMicUI(active) {
    const btnMic = document.getElementById('btn-mic-action');
    if (btnMic) {
      if (active) btnMic.classList.add('listening');
      else btnMic.classList.remove('listening');
    }
    const btnHeaderMic = document.getElementById('btn-mic-toggle');
    if (btnHeaderMic) {
      if (active) btnHeaderMic.classList.add('listening');
      else btnHeaderMic.classList.remove('listening');
    }
  }

  startListening() {
    this.isListening = true;
    this.syncMicUI(true);
    this.safeStartRecognizer();
  }

  stopListening() {
    this.isListening = false;
    clearTimeout(this._restartTimer);
    this._isRecognizerActive = false;
    this._isStarting = false;
    this.syncMicUI(false);

    if (this.speechRecognizer) {
      try {
        this.speechRecognizer.abort();
      } catch (e) {}
    }
  }

  toggleListening() {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  toggleLanguageMode() {
    // Cycle between: 'auto' (EN / తెలుగు) -> 'te' (తెలుగు) -> 'en' (English)
    if (this.currentLangMode === 'auto') {
      this.currentLangMode = 'te';
    } else if (this.currentLangMode === 'te') {
      this.currentLangMode = 'en';
    } else {
      this.currentLangMode = 'auto';
    }
    localStorage.setItem('doom_lang_mode', this.currentLangMode);
    this.updateLangUI();

    // Reconfigure speech recognition locale
    if (this.speechRecognizer) {
      const targetLocale = this.currentLangMode === 'te' ? 'te-IN' : 'en-IN';
      if (this.speechRecognizer.lang !== targetLocale) {
        this.speechRecognizer.lang = targetLocale;
        if (this._isRecognizerActive) {
          try { this.speechRecognizer.abort(); } catch (e) {}
        }
      }
    }
  }

  updateLangUI() {
    const txt = document.getElementById('hud-lang-text');
    const btn = document.getElementById('btn-lang-toggle');
    if (!txt || !btn) return;
    if (this.currentLangMode === 'te') {
      txt.innerText = 'తెలుగు (TE)';
      btn.classList.add('telugu-active');
      btn.title = 'Current Speech Input: Native Telugu (te-IN). Click to switch.';
    } else if (this.currentLangMode === 'en') {
      txt.innerText = 'ENGLISH (EN)';
      btn.classList.remove('telugu-active');
      btn.title = 'Current Speech Input: English (en-IN). Click to switch.';
    } else {
      txt.innerText = 'EN / తెలుగు';
      btn.classList.remove('telugu-active');
      btn.title = 'Current Speech Input: Bilingual Auto (English & Telugu). Click to toggle.';
    }
  }

  initUIEvents() {

    // Microphone action button
    const btnMicAction = document.getElementById('btn-mic-action');
    if (btnMicAction) {
      btnMicAction.addEventListener('click', () => this.toggleListening());
    }

    const btnHeaderMic = document.getElementById('btn-mic-toggle');
    if (btnHeaderMic) {
      btnHeaderMic.addEventListener('click', () => this.toggleListening());
    }

    // Bilingual Language Mode Toggle
    const btnLangToggle = document.getElementById('btn-lang-toggle');
    if (btnLangToggle) {
      btnLangToggle.addEventListener('click', () => this.toggleLanguageMode());
    }
    this.updateLangUI();


    // Clear dialogue stream button
    const btnClearTranscript = document.getElementById('btn-clear-transcript');
    if (btnClearTranscript) {
      btnClearTranscript.addEventListener('click', () => this._clearTranscriptHistory());
    }

    // Text command execution (Supports big multi-sentence commands and Up/Down history cycling)
    const inputCmd = document.getElementById('text-command-input');
    const btnSubmit = document.getElementById('btn-submit-command');

    const submitAction = () => {
      const text = inputCmd.value.trim();
      if (!text) return;

      // Add to input command history for ArrowUp / ArrowDown navigation (No limit)
      if (!this.inputCommandHistory.includes(text)) {
        this.inputCommandHistory.push(text);
      }
      this.inputHistoryIndex = -1;

      inputCmd.value = '';
      this.updateTranscript('MASTER', `"${text}"`);
      this.commandCount++;
      this.updateCommandCount(this.commandCount);

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'command',
          data: { command: text }
        }));
      } else {
        // Fallback REST call
        fetch('/api/command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: text, is_voice: false })
        });
      }
    };

    if (btnSubmit) btnSubmit.addEventListener('click', submitAction);
    if (inputCmd) {
      inputCmd.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          submitAction();
        } else if (e.key === 'ArrowUp') {
          if (this.inputCommandHistory.length > 0) {
            e.preventDefault();
            if (this.inputHistoryIndex < this.inputCommandHistory.length - 1) {
              this.inputHistoryIndex++;
            }
            inputCmd.value = this.inputCommandHistory[this.inputCommandHistory.length - 1 - this.inputHistoryIndex];
          }
        } else if (e.key === 'ArrowDown') {
          if (this.inputHistoryIndex > 0) {
            e.preventDefault();
            this.inputHistoryIndex--;
            inputCmd.value = this.inputCommandHistory[this.inputCommandHistory.length - 1 - this.inputHistoryIndex];
          } else if (this.inputHistoryIndex === 0) {
            e.preventDefault();
            this.inputHistoryIndex = -1;
            inputCmd.value = '';
          }
        }
      });
    }

    // Dedicated AI Chat Mute button (only mutes chat voice responses)
    const btnMuteChat = document.getElementById('btn-mute-chat');
    const updateChatMuteUI = (muted) => {
      if (!btnMuteChat) return;
      if (muted) {
        btnMuteChat.innerText = '🔇';
        btnMuteChat.classList.add('muted');
        btnMuteChat.title = 'Unmute AI Chat Voice (Chat Only)';
      } else {
        btnMuteChat.innerText = '🔊';
        btnMuteChat.classList.remove('muted');
        btnMuteChat.title = 'Mute AI Chat Voice (Chat Only)';
      }
    };

    updateChatMuteUI(this.isChatMuted);

    if (btnMuteChat) {
      btnMuteChat.addEventListener('click', () => {
        this.isChatMuted = !this.isChatMuted;
        localStorage.setItem('doom_ai_chat_muted', this.isChatMuted ? '1' : '0');
        updateChatMuteUI(this.isChatMuted);

        // Notify backend over WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({
            type: 'set_chat_mute',
            data: { muted: this.isChatMuted }
          }));
          if (this.isChatMuted) {
            this.ws.send(JSON.stringify({ type: 'stop_tts' }));
          }
        }
        // Fallback REST call
        fetch('/api/chat/mute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ muted: this.isChatMuted })
        }).catch(() => {});

        this.updateTranscript('DOOM', this.isChatMuted ? '"AI Chat voice muted. (App & system commands remain audible.)"' : '"AI Chat voice unmuted."');
      });
    }

    // Copy AI Answer button
    const btnCopyAnswer = document.getElementById('btn-copy-answer');
    if (btnCopyAnswer) {
      btnCopyAnswer.addEventListener('click', () => {
        const answerBody = document.getElementById('ai-answer-body');
        if (answerBody && answerBody.innerText) {
          navigator.clipboard.writeText(answerBody.innerText).then(() => {
            const orig = btnCopyAnswer.innerText;
            btnCopyAnswer.innerText = '✓';
            setTimeout(() => { btnCopyAnswer.innerText = orig; }, 1600);
          });
        }
      });
    }

    // Clear AI Answer button
    const btnClearAnswer = document.getElementById('btn-clear-answer');
    if (btnClearAnswer) {
      btnClearAnswer.addEventListener('click', () => {
        const qLine = document.getElementById('ai-question-line');
        const ansBody = document.getElementById('ai-answer-body');
        const srcBox = document.getElementById('ai-answer-source');
        const disp = document.getElementById('ai-answer-displayer');
        const lBadge = document.getElementById('ai-lang-badge');

        if (qLine) qLine.innerText = 'Ask any question or say a command...';
        if (ansBody) ansBody.innerText = 'Ask Doom anything — questions, code generation, programming explanations, or system commands. Spoken and typed answers will appear formatted here in real time.';
        if (srcBox) srcBox.classList.add('hidden');
        if (disp) disp.classList.remove('has-answer');
        if (lBadge) lBadge.innerText = 'READY';
      });
    }

    // Automatically activate microphone listening for hands-free wake word
    setTimeout(() => {
      this.startListening();
    }, 1000);
  }
}

// Instantiate application on load
window.doomApp = null;
window.vikramApp = null;
document.addEventListener('DOMContentLoaded', () => {
  window.doomApp = new VikramApp();
  window.vikramApp = window.doomApp;
});
