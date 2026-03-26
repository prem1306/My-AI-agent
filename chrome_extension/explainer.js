/**
 * explainer.js
 * Handles the Gemini text explainer overlay injected into web pages.
 * Triggered by: Shift+E (on selected text) or Shift+S (for summary)
 */

// ── Keyboard Shortcuts ────────────────────────────────────────────────────────
document.addEventListener('keydown', function (event) {
    // Shift+E → Explain
    if (event.shiftKey && !event.ctrlKey && (event.key === 'E' || event.key === 'e')) {
        const selection = window.getSelection().toString().trim();
        if (selection.length > 0) {
            showLoadingOverlay("Analyzing text...");
            safeSendMessage({ action: "explain_text", text: selection });
        }
    }
    // Shift+S → Summarize
    if (event.shiftKey && !event.ctrlKey && (event.key === 'S' || event.key === 's')) {
        const selection = window.getSelection().toString().trim();
        if (selection.length > 0) {
            showLoadingOverlay("Summarizing...");
            safeSendMessage({ action: "summarize_text", text: selection });
        }
    }
}, true);

// ── Message Listener ──────────────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "show_explanation") {
        updateOverlay(request.explanation, request.mode || "explain");
    }
    if (request.action === "show_summary") {
        updateOverlay(request.summary, "summarize");
    }
    if (request.action === "show_translation") {
        updateOverlay(`🌐 <em>${request.target_language}</em>\n\n${request.translation}`, "translate");
    }
    if (request.action === "show_error") {
        showErrorOverlay(request.message);
    }
});

// ── Safe Message Send ─────────────────────────────────────────────────────────
function safeSendMessage(msg) {
    try {
        chrome.runtime.sendMessage(msg);
    } catch (e) {
        console.error("Agent Extension: Could not send message", e);
        alert("The extension has been updated. Please refresh this page.");
        removeOverlay();
    }
}

// ── Overlay UI ────────────────────────────────────────────────────────────────
function showLoadingOverlay(loadingText = "Working...") {
    removeOverlay();
    injectOverlayStyles();

    const overlay = document.createElement('div');
    overlay.id = 'agent-explainer-overlay';
    overlay.className = 'agent-overlay';

    overlay.innerHTML = `
        <div class="agent-overlay-header">
            <div class="agent-overlay-header-title">
                ${getAgentIcon()}
                <span>AI Agent</span>
            </div>
            <button class="agent-overlay-close" id="agent-overlay-close">✕</button>
        </div>
        <div class="agent-overlay-body" id="agent-overlay-body">
            <div class="agent-loading">
                <div class="agent-spinner"></div>
                <span>${loadingText}</span>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
    makeDraggable(overlay);
    document.getElementById('agent-overlay-close').addEventListener('click', removeOverlay);
}

function updateOverlay(content, mode = "explain") {
    let bodyEl = document.getElementById('agent-overlay-body');
    if (!bodyEl) {
        showLoadingOverlay();
        bodyEl = document.getElementById('agent-overlay-body');
    }

    // Update header title icon based on mode
    const headerTitle = document.querySelector('.agent-overlay-header-title span');
    if (headerTitle) {
        const titles = { explain: "Explanation", summarize: "Summary", translate: "Translation" };
        headerTitle.textContent = titles[mode] || "AI Agent";
    }

    // Render markdown-like formatting
    const formatted = renderMarkdown(content);

    bodyEl.innerHTML = `
        <div class="agent-content">${formatted}</div>
        <div class="agent-actions">
            ${mode !== 'explain' ? '' : `<button class="agent-action-btn" id="agent-btn-textbook">📚 Detailed</button>`}
            ${mode !== 'summarize' ? `<button class="agent-action-btn" id="agent-btn-summarize">📋 Summarize</button>` : ''}
            <button class="agent-action-btn" id="agent-btn-translate">🌐 Translate</button>
            <button class="agent-action-btn agent-btn-copy" id="agent-btn-copy">Copy</button>
        </div>
    `;

    // Hook up action buttons
    document.getElementById('agent-btn-copy')?.addEventListener('click', () => {
        navigator.clipboard.writeText(content).then(() => {
            const btn = document.getElementById('agent-btn-copy');
            if (btn) { btn.textContent = "✓ Copied!"; setTimeout(() => { btn.textContent = "Copy"; }, 2000); }
        });
    });

    const lastText = window._agentLastText || "";

    document.getElementById('agent-btn-textbook')?.addEventListener('click', () => {
        showLoadingOverlay("Getting detailed explanation...");
        safeSendMessage({ action: "explain_text", text: lastText, style: "textbook" });
    });
    document.getElementById('agent-btn-summarize')?.addEventListener('click', () => {
        showLoadingOverlay("Summarizing...");
        safeSendMessage({ action: "summarize_text", text: lastText });
    });
    document.getElementById('agent-btn-translate')?.addEventListener('click', () => {
        const lang = prompt("Translate to (e.g. Spanish, French, Hindi, Japanese):", "Spanish");
        if (lang) {
            showLoadingOverlay(`Translating to ${lang}...`);
            safeSendMessage({ action: "translate_text", text: lastText, target_language: lang.toLowerCase() });
        }
    });
}

function showErrorOverlay(message) {
    const bodyEl = document.getElementById('agent-overlay-body');
    if (bodyEl) {
        bodyEl.innerHTML = `<div class="agent-error">⚠️ ${message}</div>`;
    } else {
        showLoadingOverlay("Error");
        const b = document.getElementById('agent-overlay-body');
        if (b) b.innerHTML = `<div class="agent-error">⚠️ ${message}</div>`;
    }
}

function removeOverlay() {
    document.getElementById('agent-explainer-overlay')?.remove();
}

// ── Draggable ─────────────────────────────────────────────────────────────────
function makeDraggable(el) {
    const header = el.querySelector('.agent-overlay-header');
    let isDragging = false, offsetX = 0, offsetY = 0;

    header.style.cursor = 'grab';
    header.addEventListener('mousedown', (e) => {
        isDragging = true;
        offsetX = e.clientX - el.getBoundingClientRect().left;
        offsetY = e.clientY - el.getBoundingClientRect().top;
        header.style.cursor = 'grabbing';
    });
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        el.style.left = (e.clientX - offsetX) + 'px';
        el.style.top = (e.clientY - offsetY) + 'px';
        el.style.right = 'auto';
    });
    document.addEventListener('mouseup', () => {
        isDragging = false;
        header.style.cursor = 'grab';
    });
}

// ── Markdown Renderer ─────────────────────────────────────────────────────────
function renderMarkdown(text) {
    return text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') // escape HTML
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')               // bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>')                           // italic
        .replace(/`(.*?)`/g, '<code>$1</code>')                         // inline code
        .replace(/^#{1,3}\s+(.+)$/gm, '<h4>$1</h4>')                   // headings
        .replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>')                    // bullets
        .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')                     // wrap list
        .replace(/\n\n/g, '</p><p>')                                    // paragraphs
        .replace(/\n/g, '<br>');                                        // line breaks
}

function getAgentIcon() {
    return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" fill="#4285F4"/>
        <path d="M11 7h2v6h-2zm0 8h2v2h-2z" fill="#4285F4"/>
    </svg>`;
}

// ── CSS Injection ─────────────────────────────────────────────────────────────
function injectOverlayStyles() {
    if (document.getElementById('agent-overlay-styles')) return;
    const style = document.createElement('style');
    style.id = 'agent-overlay-styles';
    style.textContent = `
        .agent-overlay {
            position: fixed; top: 20px; right: 20px;
            width: 360px; max-height: 80vh;
            background: #fff; border-radius: 14px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.08);
            z-index: 2147483647; font-family: 'Google Sans', Roboto, Arial, sans-serif;
            color: #202124; display: flex; flex-direction: column;
            overflow: hidden; animation: agentSlideIn 0.25s ease;
        }
        @keyframes agentSlideIn {
            from { opacity: 0; transform: translateY(-12px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .agent-overlay-header {
            background: #f8f9fa; padding: 10px 14px;
            border-bottom: 1px solid #dadce0;
            display: flex; justify-content: space-between; align-items: center;
            user-select: none;
        }
        .agent-overlay-header-title {
            display: flex; align-items: center; gap: 8px;
            font-weight: 600; font-size: 14px; color: #1a73e8;
        }
        .agent-overlay-close {
            background: none; border: none; cursor: pointer;
            color: #5f6368; font-size: 16px; padding: 4px 8px;
            border-radius: 50%; transition: background 0.2s;
        }
        .agent-overlay-close:hover { background: #e8eaed; }
        .agent-overlay-body {
            flex: 1; overflow-y: auto; padding: 16px;
        }
        .agent-loading {
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            gap: 12px; color: #5f6368; padding: 20px 0;
        }
        .agent-spinner {
            width: 28px; height: 28px;
            border: 3px solid #f0f0f0; border-top: 3px solid #4285f4;
            border-radius: 50%; animation: agentSpin 0.8s linear infinite;
        }
        @keyframes agentSpin { to { transform: rotate(360deg); } }
        .agent-content {
            font-size: 14px; line-height: 1.7; color: #202124; word-break: break-word;
        }
        .agent-content ul { padding-left: 18px; margin: 6px 0; }
        .agent-content li { margin-bottom: 4px; }
        .agent-content h4 { margin: 10px 0 4px; color: #1a73e8; font-size: 14px; }
        .agent-content code {
            background: #f1f3f4; padding: 2px 6px;
            border-radius: 4px; font-size: 13px; font-family: monospace;
        }
        .agent-content strong { font-weight: 600; }
        .agent-actions {
            margin-top: 14px; padding-top: 10px;
            border-top: 1px solid #f1f3f4;
            display: flex; gap: 6px; flex-wrap: wrap;
        }
        .agent-action-btn {
            padding: 5px 12px; border: 1px solid #dadce0; border-radius: 16px;
            background: #fff; color: #1a73e8; font-size: 12px; font-weight: 500;
            cursor: pointer; transition: background 0.2s, box-shadow 0.2s;
        }
        .agent-action-btn:hover { background: #e8f0fe; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }
        .agent-btn-copy { margin-left: auto; color: #5f6368; border-color: #e8eaed; }
        .agent-error {
            color: #d93025; background: #fce8e6; padding: 12px; border-radius: 8px;
            font-size: 13px;
        }
    `;
    document.head.appendChild(style);
}

// Store last selected text for action buttons
document.addEventListener('mouseup', () => {
    const sel = window.getSelection().toString().trim();
    if (sel) window._agentLastText = sel;
});
