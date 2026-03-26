/**
 * popup.js (v2)
 * Drives the redesigned popup: status check, history display, open chat button.
 */

document.addEventListener('DOMContentLoaded', () => {
    const statusDot   = document.getElementById('status-dot');
    const statusLabel = document.getElementById('status-label');
    const statusAgents = document.getElementById('status-agents');
    const historyList = document.getElementById('history-list');
    const openChatBtn = document.getElementById('open-chat');

    // ── Server Status Check ───────────────────────────────────────────────────
    chrome.runtime.sendMessage({ action: "check_server" }, (response) => {
        if (chrome.runtime.lastError || !response) {
            setStatus(false, []);
            return;
        }
        setStatus(response.online, response.agents || []);
    });

    function setStatus(online, agents) {
        statusDot.className = `status-dot ${online ? 'online' : 'offline'}`;
        statusLabel.textContent = online ? 'Server Online' : 'Server Offline';
        if (online && agents.length > 0) {
            statusAgents.textContent = `${agents.length} agents`;
        }
    }

    // ── Recent History ────────────────────────────────────────────────────────
    fetch("http://localhost:8000/history?limit=5")
        .then(r => r.json())
        .then(data => {
            const items = data.history || [];
            if (items.length === 0) return;
            historyList.innerHTML = '';
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'history-item';
                const text = (item.input_text || '').substring(0, 60);
                const ts   = new Date(item.timestamp + 'Z').toLocaleTimeString();
                div.innerHTML = `
                    <span class="agent-badge">${item.agent_type}</span>${text}...
                    <span class="ts">${ts}</span>
                `;
                historyList.appendChild(div);
            });
        })
        .catch(() => {}); // Server might be offline

    // ── Open Chat Button ──────────────────────────────────────────────────────
    openChatBtn.addEventListener('click', () => {
        const url = chrome.runtime.getURL("popup_interactive.html");
        chrome.windows.create({ url, type: "popup", width: 480, height: 640 });
    });
});
