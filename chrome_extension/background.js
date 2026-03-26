/**
 * background.js (v2)
 * Service worker: handles messages from explainer.js, command_center.js,
 * context menu, and mediates calls to the FastAPI backend.
 */

const SERVER = "http://localhost:8000";

// ── Context Menu ──────────────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "explain-selection",
        title: "✨ Explain with AI Agent",
        contexts: ["selection"]
    });
    chrome.contextMenus.create({
        id: "summarize-selection",
        title: "📋 Summarize with AI Agent",
        contexts: ["selection"]
    });
    chrome.contextMenus.create({
        id: "translate-selection",
        title: "🌐 Translate with AI Agent",
        contexts: ["selection"]
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (!info.selectionText || !tab?.id) return;
    const text = info.selectionText;

    if (info.menuItemId === "explain-selection") {
        chrome.storage.local.set({ last_text: text, last_explanation: "Loading..." });
        fetchExplanation(text, tab.id, "simple");
    }
    if (info.menuItemId === "summarize-selection") {
        fetchSummary(text, tab.id);
    }
    if (info.menuItemId === "translate-selection") {
        // Open interactive popup for translation (needs language selection)
        openInteractivePopup(text);
    }
});

// ── Message Router ────────────────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const tabId = sender.tab?.id || null;

    if (request.action === "explain_text") {
        chrome.storage.local.set({ last_text: request.text, last_explanation: "Loading..." });
        fetchExplanation(request.text, tabId, request.style || "simple");
    }

    if (request.action === "summarize_text") {
        fetchSummary(request.text, tabId, request.length || "medium");
    }

    if (request.action === "translate_text") {
        fetchTranslation(request.text, tabId, request.target_language || "spanish");
    }

    if (request.action === "execute_command") {
        executeCommand(request.command).then(sendResponse);
        return true; // async
    }

    if (request.action === "check_server") {
        checkServer().then(sendResponse);
        return true; // async
    }
});

// ── API Calls ─────────────────────────────────────────────────────────────────
async function fetchExplanation(text, tabId, style = "simple") {
    try {
        const response = await fetchWithTimeout(`${SERVER}/explain`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, style, history: [] })
        });
        const data = await response.json();
        if (response.ok && data.status === "success") {
            chrome.storage.local.set({ last_explanation: data.explanation });
            sendToTab(tabId, { action: "show_explanation", explanation: data.explanation, mode: "explain" });
        } else {
            sendToTab(tabId, { action: "show_error", message: data.detail || data.message || "Unknown error" });
        }
    } catch (e) {
        sendToTab(tabId, { action: "show_error", message: "Cannot reach server at localhost:8000. Is it running?" });
    }
}

async function fetchSummary(text, tabId, length = "medium") {
    try {
        const response = await fetchWithTimeout(`${SERVER}/summarize`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, length })
        });
        const data = await response.json();
        if (response.ok && data.status === "success") {
            sendToTab(tabId, { action: "show_summary", summary: data.summary });
        } else {
            sendToTab(tabId, { action: "show_error", message: data.detail || "Summarization failed" });
        }
    } catch (e) {
        sendToTab(tabId, { action: "show_error", message: "Cannot reach server. Is it running?" });
    }
}

async function fetchTranslation(text, tabId, target_language = "spanish") {
    try {
        const response = await fetchWithTimeout(`${SERVER}/translate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, target_language })
        });
        const data = await response.json();
        if (response.ok && data.status === "success") {
            sendToTab(tabId, {
                action: "show_translation",
                translation: data.translation,
                target_language: data.target_language
            });
        } else {
            sendToTab(tabId, { action: "show_error", message: data.detail || "Translation failed" });
        }
    } catch (e) {
        sendToTab(tabId, { action: "show_error", message: "Cannot reach server. Is it running?" });
    }
}

async function executeCommand(command) {
    try {
        const response = await fetchWithTimeout(`${SERVER}/execute`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command })
        });
        const data = await response.json();
        return { result: data.result || data.message || "Done." };
    } catch (e) {
        return { result: "Error: " + e.message };
    }
}

async function checkServer() {
    try {
        const response = await fetchWithTimeout(`${SERVER}/health`, {}, 3000);
        const data = await response.json();
        return { online: true, agents: data.agents || [] };
    } catch (e) {
        return { online: false, agents: [] };
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
async function fetchWithTimeout(url, options = {}, timeout = 12000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
        return await fetch(url, { ...options, signal: controller.signal });
    } finally {
        clearTimeout(id);
    }
}

function sendToTab(tabId, message) {
    if (!tabId) {
        // Try active tab
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) chrome.tabs.sendMessage(tabs[0].id, message).catch(() => {});
        });
        return;
    }
    chrome.tabs.sendMessage(tabId, message).catch(() => {
        // Content script not ready — open popup fallback
        if (message.explanation || message.summary) {
            openInteractivePopup(message.explanation || message.summary);
        }
    });
}

function openInteractivePopup(text) {
    const url = chrome.runtime.getURL("popup_interactive.html") +
        "?text=" + encodeURIComponent(text.substring(0, 2000));
    chrome.windows.create({ url, type: "popup", width: 480, height: 640 });
}
