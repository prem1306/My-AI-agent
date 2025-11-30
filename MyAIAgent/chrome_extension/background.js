// Background script to handle messages and API calls

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "explain_text") {
        console.log("Received text to explain:", request.text);
        chrome.storage.local.set({ "last_explanation": "Loading...", "last_text": request.text });
        fetchExplanation(request.text);
        // explain_text uses a separate UI overlay flow, so we don't use sendResponse here for the content
    }

    if (request.action === "execute_command") {
        console.log("Executing command:", request.command);
        // Return true to indicate we will send a response asynchronously
        executeCommand(request.command).then(sendResponse);
        return true;
    }
});

async function fetchExplanation(text) {
    try {
        const response = await fetch("http://localhost:8000/explain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();

        if (data.status === "success") {
            chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
                if (tabs[0]) {
                    chrome.tabs.sendMessage(tabs[0].id, {
                        action: "show_overlay",
                        explanation: data.explanation
                    });
                }
            });
        } else {
            sendErrorToUI(data.message || "Unknown Agent Error");
        }
    } catch (error) {
        sendErrorToUI("Network Error: Is the server running? Check console.");
    }
}

async function executeCommand(command) {
    try {
        const response = await fetch("http://localhost:8000/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: command })
        });

        const data = await response.json();
        return { result: data.result || data.message };
    } catch (error) {
        console.error("Command Error:", error);
        return { result: "Error: " + error.message };
    }
}

function sendErrorToUI(message) {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, {
                action: "show_overlay",
                explanation: "Error: " + message
            });
        }
    });
}
