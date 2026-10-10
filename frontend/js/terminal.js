/**
 * DOOM AI - Console & Terminal Manager
 * Handles tab switching, Developer Mode compilation inspector, and Command History stream.
 */

class TerminalManager {
  constructor() {
    this.initTabs();
    this.initHistory();
    this.initSettings();
  }

  initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.tab;
        this.switchTab(target);
      });
    });

    // Quick header action buttons
    const btnDev = document.getElementById('btn-tab-dev');
    if (btnDev) btnDev.addEventListener('click', () => this.switchTab('dev'));

    const btnHist = document.getElementById('btn-tab-history');
    if (btnHist) btnHist.addEventListener('click', () => this.switchTab('history'));

    const btnSet = document.getElementById('btn-tab-settings');
    if (btnSet) btnSet.addEventListener('click', () => this.switchTab('settings'));
  }

  switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach((b) => {
      b.classList.toggle('active', b.dataset.tab === tabName);
    });

    document.querySelectorAll('.tab-content').forEach((c) => {
      c.classList.toggle('active', c.id === `tab-content-${tabName}`);
    });
  }

  logToTerminal(text) {
    const term = document.getElementById('terminal-output');
    if (term) {
      term.textContent += `\n${text}`;
      term.scrollTop = term.scrollHeight;
    }
  }

  updateDeveloperOutput(details) {
    if (!details) return;

    this.switchTab('dev');
    const term = document.getElementById('terminal-output');
    const inspector = document.getElementById('error-inspector');
    const errFileLine = document.getElementById('err-file-line');
    const errDetails = document.getElementById('err-details-text');
    const fixBox = document.getElementById('err-fix-box');
    const fixText = document.getElementById('err-fix-text');

    const status = details.status || (details.compilation && details.compilation.status);

    if (status === 'ERROR' || status === 'RUNTIME_ERROR') {
      if (inspector) inspector.classList.add('has-error');
      const diag = details.diagnosis || (details.compilation && details.compilation.diagnosis) || {};
      
      if (errFileLine) errFileLine.innerText = `ERROR // ${diag.file || details.file || 'File'} : Line ${diag.line || '?'}`;
      if (errDetails) errDetails.innerText = diag.explanation || details.stderr || details.error || 'Compiler error detected.';

      if (fixBox && fixText) {
        if (diag.suggested_fix) {
          fixBox.classList.remove('hidden');
          fixText.innerText = diag.suggested_fix;
        } else {
          fixBox.classList.add('hidden');
        }
      }

      this.logToTerminal(`\n[COMPILER ERROR] in ${details.file || ''}:\n${details.stderr || ''}`);
    } else if (status === 'SUCCESS') {
      if (inspector) inspector.classList.remove('has-error');
      if (errFileLine) errFileLine.innerText = `SUCCESS // ${details.file || 'Code'}`;
      if (errDetails) errDetails.innerText = 'Compilation / execution completed with exit code 0.';
      if (fixBox) fixBox.classList.add('hidden');

      if (details.stdout) {
        this.logToTerminal(`\n[EXECUTION OUTPUT]:\n${details.stdout}`);
      }
    }
  }

  async initHistory() {
    const btnClear = document.getElementById('btn-clear-history');
    if (btnClear) {
      btnClear.addEventListener('click', async () => {
        await fetch('/api/history', { method: 'DELETE' });
        const stream = document.getElementById('history-stream');
        if (stream) stream.innerHTML = '<div class="history-item">History cleared.</div>';
        if (window.doomApp && typeof window.doomApp.updateCommandCount === 'function') {
          window.doomApp.updateCommandCount(0);
        }
      });
    }
    this.fetchHistory();
  }

  async fetchHistory() {
    try {
      const res = await fetch('/api/history');
      const items = await res.json();
      const stream = document.getElementById('history-stream');
      if (!stream) return;

      stream.innerHTML = '';
      items.forEach((item) => this.appendHistoryItem(item));
    } catch (e) {
      console.warn('History fetch notice:', e);
    }
  }

  appendHistoryItem(item) {
    const stream = document.getElementById('history-stream');
    if (!stream) return;

    const div = document.createElement('div');
    div.className = 'history-item';
    const timeStr = item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : '';

    div.innerHTML = `
      <div class="history-time">${timeStr} // ${item.intent || 'COMMAND'}</div>
      <div class="history-user">User: ${item.raw_command}</div>
      <div class="history-doom">DOOM: ${item.doom_response || item.vikram_response}</div>
    `;
    stream.insertBefore(div, stream.firstChild);
  }

  initSettings() {
    const btnReset = document.getElementById('btn-reset-pairing');
    if (btnReset) {
      btnReset.addEventListener('click', async () => {
        if (confirm('Are you sure you want to reset DOOM AI and unpair this device?')) {
          await fetch('/api/setup/pair', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reset: true })
          });
          window.location.reload();
        }
      });
    }

    const btnReEnroll = document.getElementById('btn-re-enroll-voice');
    if (btnReEnroll && window.setupWizard) {
      btnReEnroll.addEventListener('click', () => {
        window.setupWizard.show();
        window.setupWizard.goToStep(4);
      });
    }

    // Google Gemini API Key Settings
    const inputGeminiKey = document.getElementById('set-gemini-key');
    const btnSaveGemini = document.getElementById('btn-save-gemini-key');
    const btnClearGemini = document.getElementById('btn-clear-gemini-key');
    const modeText = document.getElementById('gemini-mode-text');

    const loadGeminiSettings = async () => {
      try {
        const res = await fetch('/api/settings');
        if (res.ok) {
          const settings = await res.json();
          const key = (settings.gemini_api_key || '').trim();
          if (key) {
            if (inputGeminiKey) inputGeminiKey.value = key;
            if (modeText) {
              modeText.innerText = 'Google Gemini Cloud (Active)';
              modeText.style.color = '#38ef7d';
            }
            if (btnClearGemini) btnClearGemini.style.display = 'inline-block';
          } else {
            if (inputGeminiKey) inputGeminiKey.value = '';
            if (modeText) {
              modeText.innerText = 'Gemini Synthesizer (Active)';
              modeText.style.color = '#1fe376';
            }
            if (btnClearGemini) btnClearGemini.style.display = 'none';
          }
        }
      } catch (e) {
        console.debug('Failed to load settings:', e);
      }
    };

    loadGeminiSettings();

    if (btnSaveGemini) {
      btnSaveGemini.addEventListener('click', async () => {
        const key = (inputGeminiKey ? inputGeminiKey.value : '').trim();
        if (!key) {
          alert('Please enter a valid Gemini API key.');
          return;
        }
        try {
          btnSaveGemini.disabled = true;
          btnSaveGemini.innerText = 'SAVING...';
          const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gemini_api_key: key })
          });
          if (res.ok) {
            btnSaveGemini.innerText = 'SAVED!';
            setTimeout(() => { btnSaveGemini.innerText = 'SAVE'; btnSaveGemini.disabled = false; }, 1500);
            loadGeminiSettings();
          } else {
            alert('Failed to save Gemini API key.');
            btnSaveGemini.innerText = 'SAVE';
            btnSaveGemini.disabled = false;
          }
        } catch (err) {
          alert('Error saving settings: ' + err);
          btnSaveGemini.innerText = 'SAVE';
          btnSaveGemini.disabled = false;
        }
      });
    }

    if (btnClearGemini) {
      btnClearGemini.addEventListener('click', async () => {
        if (confirm('Disconnect Gemini Cloud API key and revert to Gemini Synthesizer mode?')) {
          await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gemini_api_key: '' })
          });
          loadGeminiSettings();
        }
      });
    }
  }
}

window.terminalManager = null;
document.addEventListener('DOMContentLoaded', () => {
  window.terminalManager = new TerminalManager();
});
