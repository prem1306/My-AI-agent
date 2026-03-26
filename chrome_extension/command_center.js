/**
 * command_center.js
 * Handles the Ctrl+Shift+Q command center overlay.
 * Clean terminal-style UI with command history (↑/↓), autocomplete hints.
 */

const COMMANDS_HINT = [
    "open notepad", "open calc", "open explorer",
    "open folder <name>", "create folder <name>", "delete folder <name>",
    "list sandbox", "run dir", "run echo hello",
    "history", "agents", "help"
];

// ── Keyboard Shortcut ─────────────────────────────────────────────────────────
document.addEventListener('keydown', function (event) {
    if (event.ctrlKey && event.shiftKey && (event.key === 'Q' || event.key === 'q')) {
        event.preventDefault();
        toggleCommandCenter();
    }
}, true);

// ── Message Listener ──────────────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "command_result") {
        appendCommandLog(request.result, "result");
    }
});

// ── State ─────────────────────────────────────────────────────────────────────
let commandHistory = [];
let historyIndex = -1;

// ── Toggle ────────────────────────────────────────────────────────────────────
function toggleCommandCenter() {
    const existing = document.getElementById('agent-command-center');
    if (existing) { existing.remove(); return; }
    buildCommandCenter();
}

function buildCommandCenter() {
    injectCommandCenterStyles();

    const overlay = document.createElement('div');
    overlay.id = 'agent-command-center';

    overlay.innerHTML = `
        <div id="acc-header">
            <div id="acc-title">
                <span id="acc-title-dot"></span>
                <span>&gt;_  AI Agent Command Center</span>
            </div>
            <button id="acc-close">✕</button>
        </div>
        <div id="acc-output">
            <div class="acc-line acc-comment"># System Ready — Ctrl+Shift+Q to toggle</div>
            <div class="acc-line acc-comment"># Shift+E = Explain  |  Shift+S = Summarize  |  Ctrl+Shift+Q = Command Center</div>
            <div class="acc-line acc-comment"># Type "help" for a list of commands</div>
        </div>
        <div id="acc-input-row">
            <span id="acc-prompt">$ </span>
            <input id="acc-input" type="text" placeholder="Type command..." autocomplete="off" spellcheck="false" />
        </div>
        <div id="acc-hints"></div>
    `;

    document.body.appendChild(overlay);

    const input = document.getElementById('acc-input');
    const output = document.getElementById('acc-output');
    const hints = document.getElementById('acc-hints');

    input.focus();
    document.getElementById('acc-close').addEventListener('click', () => overlay.remove());

    // ── Command Input ──────────────────────────────────────────────────────────
    input.addEventListener('keydown', (e) => {
        // Submit
        if (e.key === 'Enter') {
            const cmd = input.value.trim();
            if (!cmd) return;

            commandHistory.unshift(cmd);
            historyIndex = -1;

            appendCommandLog(`$ ${cmd}`, "command");
            input.value = '';
            hints.innerHTML = '';

            chrome.runtime.sendMessage({
                action: "execute_command",
                command: cmd
            }, (response) => {
                if (chrome.runtime.lastError) {
                    appendCommandLog("❌ Extension error: " + chrome.runtime.lastError.message, "error");
                } else if (response?.result) {
                    appendCommandLog(response.result, "result");
                } else {
                    appendCommandLog("No response from agent.", "error");
                }
            });
        }

        // History: ↑
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (historyIndex < commandHistory.length - 1) {
                historyIndex++;
                input.value = commandHistory[historyIndex];
            }
        }

        // History: ↓
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (historyIndex > 0) {
                historyIndex--;
                input.value = commandHistory[historyIndex];
            } else if (historyIndex === 0) {
                historyIndex = -1;
                input.value = '';
            }
        }

        // Close on Esc
        if (e.key === 'Escape') overlay.remove();
    });

    // ── Autocomplete Hints ─────────────────────────────────────────────────────
    input.addEventListener('input', () => {
        const val = input.value.toLowerCase();
        hints.innerHTML = '';
        if (!val) return;
        const matches = COMMANDS_HINT.filter(c => c.startsWith(val)).slice(0, 4);
        matches.forEach(m => {
            const span = document.createElement('span');
            span.className = 'acc-hint';
            span.textContent = m;
            span.addEventListener('click', () => {
                input.value = m;
                input.focus();
                hints.innerHTML = '';
            });
            hints.appendChild(span);
        });
    });
}

function appendCommandLog(text, type = "result") {
    const output = document.getElementById('acc-output');
    if (!output) return;
    const lines = text.split('\n');
    lines.forEach(line => {
        const div = document.createElement('div');
        div.className = `acc-line acc-${type}`;
        div.textContent = line;
        output.appendChild(div);
    });
    output.scrollTop = output.scrollHeight;
}

// ── CSS ───────────────────────────────────────────────────────────────────────
function injectCommandCenterStyles() {
    if (document.getElementById('acc-styles')) return;
    const style = document.createElement('style');
    style.id = 'acc-styles';
    style.textContent = `
        #agent-command-center {
            position: fixed; top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: 560px; max-height: 480px;
            background: #1a1a2e; border: 1px solid #2d2d4e;
            box-shadow: 0 24px 60px rgba(0,0,0,0.6);
            z-index: 2147483647; border-radius: 14px;
            font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
            color: #e2e2e2; display: flex; flex-direction: column;
            overflow: hidden; animation: accSlideIn 0.2s ease;
        }
        @keyframes accSlideIn {
            from { opacity: 0; transform: translate(-50%,-52%) scale(0.97); }
            to   { opacity: 1; transform: translate(-50%,-50%) scale(1); }
        }
        #acc-header {
            background: #16213e; padding: 10px 16px;
            border-bottom: 1px solid #2d2d4e;
            display: flex; justify-content: space-between; align-items: center;
        }
        #acc-title {
            display: flex; align-items: center; gap: 10px;
            font-size: 13px; font-weight: 600; color: #7ec8e3;
        }
        #acc-title-dot {
            width: 10px; height: 10px; border-radius: 50%;
            background: #4ade80; box-shadow: 0 0 6px #4ade80;
        }
        #acc-close {
            background: none; border: none; color: #888; cursor: pointer;
            font-size: 16px; padding: 4px 8px; border-radius: 4px;
            transition: color 0.2s, background 0.2s;
        }
        #acc-close:hover { color: #fff; background: #e53e3e; }
        #acc-output {
            flex: 1; overflow-y: auto; padding: 14px 18px;
            min-height: 200px; max-height: 320px;
            scroll-behavior: smooth;
        }
        .acc-line { font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
        .acc-comment { color: #6a9955; }
        .acc-command { color: #7ec8e3; margin-top: 8px; }
        .acc-result  { color: #d4d4d4; margin-left: 14px; }
        .acc-error   { color: #f87171; margin-left: 14px; }
        #acc-input-row {
            display: flex; align-items: center;
            background: #16213e; padding: 10px 18px;
            border-top: 1px solid #2d2d4e; gap: 8px;
        }
        #acc-prompt { color: #4ade80; font-size: 14px; font-weight: 700; }
        #acc-input {
            flex: 1; background: transparent; border: none; outline: none;
            color: #e2e2e2; font-family: inherit; font-size: 14px; caret-color: #4ade80;
        }
        #acc-input::placeholder { color: #555; }
        #acc-hints {
            display: flex; gap: 6px; flex-wrap: wrap;
            padding: 0 18px 10px; background: #16213e; min-height: 0;
        }
        .acc-hint {
            padding: 3px 10px; background: #2d2d4e; border-radius: 12px;
            font-size: 11px; color: #7ec8e3; cursor: pointer;
            transition: background 0.2s;
        }
        .acc-hint:hover { background: #3d3d6e; }
    `;
    document.head.appendChild(style);
}
