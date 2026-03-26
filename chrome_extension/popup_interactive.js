/**
 * popup_interactive.js (v2)
 * Drives the AI Agent Chat popup:
 *   - Agent switcher: Explain / Summarize / Translate
 *   - Persistent chat history via chrome.storage.local
 *   - Markdown-aware message rendering
 *   - Animated loading indicator
 */

const SERVER = "http://localhost:8000";

document.addEventListener('DOMContentLoaded', () => {
    const chatHistory  = document.getElementById('chat-history');
    const userInput    = document.getElementById('user-input');
    const sendBtn      = document.getElementById('send-btn');
    const tabs         = document.querySelectorAll('.agent-tab');
    const translateBar = document.getElementById('translate-bar');
    const langSelect   = document.getElementById('lang-select');
    const headerStatus = document.getElementById('header-status');
    const contextHint  = document.getElementById('context-hint');

    let currentAgent   = 'coordinator';
    let conversationHistory = [];  // [{role, content}] for multi-turn

    const STORAGE_KEY = 'agent_chat_history';
    const AGENT_HINTS = {
        coordinator: 'Ask me to do anything. I can use tools automatically.',
        explain:   'Highlight text on any page with Shift+E, or paste text here',
        summarize: 'Paste text to get a bullet-point summary',
        translate: 'Paste text and choose a target language',
    };

    // ── Server Health ─────────────────────────────────────────────────────────
    checkServerHealth();
    function checkServerHealth() {
        fetch(`${SERVER}/health`)
            .then(r => r.json())
            .then(d => {
                headerStatus.className = 'header-status';
                contextHint.textContent = `${d.agents?.length || 0} agents online`;
            })
            .catch(() => {
                headerStatus.className = 'header-status offline';
                contextHint.textContent = 'Server offline — start run_agent.py';
            });
    }

    // ── Persistent History ────────────────────────────────────────────────────
    chrome.storage.local.get([STORAGE_KEY], (result) => {
        const saved = result[STORAGE_KEY] || [];
        saved.forEach(m => addMessageToDOM(m.role, m.content, m.label));
    });

    function persistHistory(role, content, label) {
        chrome.storage.local.get([STORAGE_KEY], (result) => {
            const arr = result[STORAGE_KEY] || [];
            arr.push({ role, content, label });
            // Keep last 40 messages
            const trimmed = arr.slice(-40);
            chrome.storage.local.set({ [STORAGE_KEY]: trimmed });
        });
    }

    // ── Agent Tabs ────────────────────────────────────────────────────────────
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentAgent = tab.dataset.agent;
            contextHint.textContent = AGENT_HINTS[currentAgent];
            conversationHistory = []; // reset multi-turn per agent switch
            translateBar.style.display = currentAgent === 'translate' ? 'block' : 'none';
        });
    });

    // ── Text Auto-resize ──────────────────────────────────────────────────────
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 80) + 'px';
    });

    // ── URL Param: pre-fill text (from content script) ────────────────────────
    const urlParams = new URLSearchParams(window.location.search);
    const initialText = urlParams.get('text');
    if (initialText) {
        userInput.value = initialText;
    }

    // ── Send ──────────────────────────────────────────────────────────────────
    sendBtn.addEventListener('click', handleSend);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
    });

    function handleSend() {
        const text = userInput.value.trim();
        if (!text || sendBtn.disabled) return;

        addMessage('user', text, currentAgent.toUpperCase());
        persistHistory('user', text, currentAgent.toUpperCase());
        userInput.value = '';
        userInput.style.height = 'auto';
        sendBtn.disabled = true;

        dispatchToAgent(text);
    }

    async function dispatchToAgent(text) {
        const loadingEl = showLoading();

        try {
            let url, body, responseKey;

            if (currentAgent === 'coordinator') {
                url = `${SERVER}/chat`;
                body = { text };
                responseKey = 'response';
            } else if (currentAgent === 'explain') {
                url = `${SERVER}/explain`;
                body = { text, style: 'simple', history: conversationHistory };
                responseKey = 'explanation';
            } else if (currentAgent === 'summarize') {
                url = `${SERVER}/summarize`;
                body = { text, length: 'medium' };
                responseKey = 'summary';
            } else if (currentAgent === 'translate') {
                url = `${SERVER}/translate`;
                body = { text, target_language: langSelect.value };
                responseKey = 'translation';
            }

            const res  = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await res.json();
            loadingEl.remove();

            if (data.status === 'success') {
                const reply = data[responseKey] || '';
                const label = currentAgent === 'translate'
                    ? `TRANSLATED → ${data.target_language || langSelect.value}`
                    : currentAgent.toUpperCase();
                addMessage('agent', reply, label);
                persistHistory('agent', reply, label);

                // Keep conversation history for explain (multi-turn)
                if (currentAgent === 'explain') {
                    conversationHistory.push({ role: 'user', content: text });
                    conversationHistory.push({ role: 'model', content: reply });
                }
            } else {
                const errMsg = data.detail || data.message || 'Unknown error';
                addMessage('agent', `⚠️ ${errMsg}`, 'ERROR');
            }
        } catch (err) {
            loadingEl.remove();
            addMessage('agent', '⚠️ Cannot reach server. Is `run_agent.py` running?', 'ERROR');
        } finally {
            sendBtn.disabled = false;
            userInput.focus();
        }
    }

    // ── DOM Helpers ───────────────────────────────────────────────────────────
    function addMessage(role, content, label = '') {
        addMessageToDOM(role, content, label);
        persistHistory(role, content, label);
    }

    function addMessageToDOM(role, content, label = '') {
        const wrapper = document.createElement('div');

        if (label) {
            const labelEl = document.createElement('div');
            labelEl.className = 'message-label';
            labelEl.textContent = label;
            labelEl.style.alignSelf = role === 'user' ? 'flex-end' : 'flex-start';
            chatHistory.appendChild(labelEl);
        }

        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.innerHTML = renderMarkdown(content);
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function showLoading() {
        const div = document.createElement('div');
        div.className = 'message agent';
        div.innerHTML = `<div class="loading-dots"><span></span><span></span><span></span></div>`;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return div;
    }

    function renderMarkdown(text) {
        return text
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/^#{1,3}\s+(.+)$/gm, '<h4>$1</h4>')
            .replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
    }
});
