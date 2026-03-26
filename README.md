# MyAIAgent 🤖

A locally-hosted multi-agent AI assistant powered by **Gemini 2.0 Flash**, with a Chrome Extension UI.

## Features

| What | How |
|---|---|
| **Explain text** | Select text on any page → `Shift+E` |
| **Summarize text** | Select text → `Shift+S` |
| **Translate text** | Right-click selection → Translate with AI Agent |
| **Command Center** | Press `Ctrl+Shift+Q` on any page |
| **Chat Interface** | Click extension icon → Open Chat Interface |

## Setup

### 1. Clone & install dependencies

```bash
cd MyAIAgent
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
copy .env.example .env
```

Edit `.env` and add your Gemini API key:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

Get a free key at: https://aistudio.google.com/app/apikey

### 3. Start the server

```bash
python run_agent.py
```

Server runs at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`

### 4. Load Chrome Extension

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer Mode** (top right)
3. Click **Load unpacked** → select the `chrome_extension/` folder
4. The 🤖 icon appears in your toolbar

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/explain` | Explain text (simple/textbook/bullet) |
| POST | `/summarize` | Summarize into bullet points (short/medium/long) |
| POST | `/translate` | Translate text to any language |
| GET  | `/translate/languages` | List supported languages |
| POST | `/execute` | Run an offline command |
| POST | `/tasks` | Manage to-do list (add/list/complete/delete) |
| GET  | `/history` | View recent interactions |
| GET  | `/health` | Server + agent status |

## Registered Agents

| Agent | Description |
|---|---|
| `GoogleExplainer` | Explains text in different styles |
| `Summarizer` | Bullet-point summaries |
| `Translator` | Translates to 12+ languages |
| `TaskAgent` | Persistent SQLite to-do list |
| `MainAgent` | Offline commands (open/create/delete) |

## Project Structure

```
MyAIAgent/
├── config.py               ← Central config (reads .env)
├── run_agent.py            ← Start the server
├── requirements.txt
├── .env.example            ← Copy to .env and fill in API key
├── main_agent/
│   ├── core.py             ← AgentBase, Registry, TaskRouter, OfflineParser
│   ├── server.py           ← FastAPI server + all routes
│   ├── tools.py            ← Sandboxed file/system operations
│   └── database.py         ← SQLite: history + tasks
├── sub_agent/
│   ├── explainer.py        ← GoogleExplainerAgent
│   ├── summarizer.py       ← SummarizerAgent
│   ├── translator.py       ← TranslatorAgent (12 languages)
│   └── task_agent.py       ← TaskAgent (to-do list)
├── chrome_extension/
│   ├── manifest.json
│   ├── background.js       ← Service worker + API calls
│   ├── explainer.js        ← In-page overlay (Shift+E / Shift+S)
│   ├── command_center.js   ← Terminal UI (Ctrl+Shift+Q)
│   ├── popup.html/js       ← Extension badge popup
│   └── popup_interactive.html/js ← Full chat interface
└── sandbox/                ← Safe zone for file operations
```
