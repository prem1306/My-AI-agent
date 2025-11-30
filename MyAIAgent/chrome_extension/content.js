// Listen for Shift+E keypress (Google Explainer)
document.addEventListener('keydown', function (event) {
    if (event.shiftKey && (event.key === 'E' || event.key === 'e')) {
        const selection = window.getSelection().toString().trim();

        if (selection.length > 0) {
            console.log("Shift+E detected. Text selected:", selection);
            showLoadingOverlay();
            chrome.runtime.sendMessage({
                action: "explain_text",
                text: selection
            });
        }
    }

    // Listen for Ctrl+Shift+Q (Main Agent Command Center)
    if (event.ctrlKey && event.shiftKey && (event.key === 'Q' || event.key === 'q')) {
        console.log("Ctrl+Shift+Q detected. Opening Command Center.");
        toggleCommandCenter();
    }
});

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "show_overlay") {
        updateOverlay(request.explanation);
    }
    if (request.action === "command_result") {
        updateCommandOutput(request.result);
    }
});

// --- Main Agent Command Center UI ---
function toggleCommandCenter() {
    const existing = document.getElementById('main-agent-overlay');
    if (existing) {
        existing.remove();
        return;
    }

    const overlay = document.createElement('div');
    overlay.id = 'main-agent-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 500px;
        background: #1e1e1e;
        border: 1px solid #333;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        z-index: 2147483647;
        border-radius: 12px;
        font-family: 'Consolas', 'Monaco', monospace;
        color: #d4d4d4;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    `;

    overlay.innerHTML = `
        <div style="background: #252526; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333;">
            <span style="font-weight: bold; color: #4ec9b0;">>_ Main Agent (Offline)</span>
            <button id="close-main-agent" style="background:none; border:none; color:#d4d4d4; cursor:pointer;">✕</button>
        </div>
        <div id="command-output" style="height: 300px; padding: 15px; overflow-y: auto; font-size: 13px; color: #cccccc;">
            <div style="color: #6a9955;"># System Ready. Waiting for commands...</div>
            <div style="color: #6a9955;"># Try: "open notepad", "create folder test", "run dir"</div>
        </div>
        <div style="padding: 10px; background: #252526; border-top: 1px solid #333; display: flex;">
            <span style="color: #4ec9b0; margin-right: 10px;">$</span>
            <input type="text" id="agent-command-input" style="
                flex: 1;
                background: transparent;
                border: none;
                color: #d4d4d4;
                font-family: inherit;
                font-size: 14px;
                outline: none;
            " placeholder="Type command..." autofocus>
        </div>
    `;

    document.body.appendChild(overlay);

    const input = document.getElementById('agent-command-input');
    input.focus();

    // Close button
    document.getElementById('close-main-agent').addEventListener('click', () => overlay.remove());

    // Submit command
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const cmd = input.value.trim();
            if (cmd) {
                appendLog(`$ ${cmd}`);
                input.value = '';

                // Send to background with callback
                chrome.runtime.sendMessage({
                    action: "execute_command",
                    command: cmd
                }, (response) => {
                    if (chrome.runtime.lastError) {
                        appendLog("Extension Error: " + chrome.runtime.lastError.message, true);
                    } else if (response && response.result) {
                        updateCommandOutput(response.result);
                    } else {
                        appendLog("No response from agent.", true);
                    }
                });
            }
        }
    });
}

function appendLog(text, isResult = false) {
    const output = document.getElementById('command-output');
    if (output) {
        const div = document.createElement('div');
        div.textContent = text;
        if (isResult) div.style.color = "#ce9178"; // reddish for results
        div.style.marginTop = "5px";
        output.appendChild(div);
        output.scrollTop = output.scrollHeight;
    }
}

function updateCommandOutput(result) {
    appendLog(result, true);
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "show_overlay") {
        updateOverlay(request.explanation);
    }
});

function showLoadingOverlay() {
    removeOverlay(); // Clear existing

    const overlay = document.createElement('div');
    overlay.id = 'google-explainer-overlay';
    // Modern Google-like styling
    overlay.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    width: 350px;
    max-height: 80vh;
    background: #ffffff;
    border: none;
    box-shadow: 0 12px 28px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.1);
    z-index: 2147483647; /* Max z-index */
    padding: 0;
    border-radius: 12px;
    font-family: 'Google Sans', Roboto, Arial, sans-serif;
    font-size: 14px;
    color: #202124;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transition: all 0.3s ease;
  `;

    // Header
    const header = `
    <div style="
      background: #f8f9fa;
      padding: 12px 16px;
      border-bottom: 1px solid #dadce0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    ">
      <div style="display: flex; align-items: center; gap: 8px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z" fill="#4285F4"/>
          <path d="M11 7H13V13H11V7ZM11 15H13V17H11V15Z" fill="#4285F4"/>
        </svg>
        <span style="font-weight: 500; color: #5f6368;">Google Explainer</span>
      </div>
      <button id="close-explainer" style="
        border: none;
        background: none;
        cursor: pointer;
        color: #5f6368;
        font-size: 18px;
        padding: 4px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
      ">✕</button>
    </div>
  `;

    // Content Area with Spinner
    const content = `
    <div id="explainer-content" style="padding: 20px; line-height: 1.6; overflow-y: auto;">
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; color: #5f6368;">
        <div class="explainer-spinner" style="
          width: 24px;
          height: 24px;
          border: 3px solid #f3f3f3;
          border-top: 3px solid #4285f4;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        "></div>
        <span>Analyzing text...</span>
      </div>
    </div>
  `;

    // Inject Styles for Spinner
    const style = document.createElement('style');
    style.textContent = `
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    #close-explainer:hover { background-color: #e8eaed; }
  `;
    document.head.appendChild(style);

    overlay.innerHTML = header + content;
    document.body.appendChild(overlay);

    document.getElementById('close-explainer').addEventListener('click', removeOverlay);
}

function updateOverlay(text) {
    const content = document.getElementById('explainer-content');
    if (content) {
        // Format the text nicely
        // 1. Handle bold text (**text**)
        let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // 2. Handle bullet points (* text)
        formatted = formatted.replace(/^\* (.*$)/gm, '• $1');
        // 3. Handle newlines
        formatted = formatted.replace(/\n/g, '<br>');

        content.innerHTML = `
      <div style="color: #202124; font-size: 14px;">
        ${formatted}
      </div>
      <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #f1f3f4; display: flex; justify-content: flex-end;">
        <button id="copy-explainer" style="
          background: #fff;
          border: 1px solid #dadce0;
          color: #1a73e8;
          padding: 6px 12px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        ">Copy</button>
      </div>
    `;

        // Add Copy Functionality
        document.getElementById('copy-explainer').addEventListener('click', () => {
            navigator.clipboard.writeText(text).then(() => {
                const btn = document.getElementById('copy-explainer');
                btn.textContent = "Copied!";
                btn.style.background = "#e8f0fe";
                setTimeout(() => {
                    btn.textContent = "Copy";
                    btn.style.background = "#fff";
                }, 2000);
            });
        });
    }
}

function removeOverlay() {
    const overlay = document.getElementById('google-explainer-overlay');
    if (overlay) {
        overlay.remove();
    }
}
