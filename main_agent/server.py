import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from main_agent.core import AgentRegistry, TaskRouter
from main_agent.database import init_db, log_interaction, get_history
from sub_agent.explainer import GoogleExplainerAgent
from sub_agent.summarizer import SummarizerAgent
from sub_agent.translator import TranslatorAgent, SUPPORTED_LANGUAGES
from sub_agent.task_agent import TaskAgent
from sub_agent.coordinator import CoordinatorAgent

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AgentServer")

# ── DB Init ──────────────────────────────────────────────────────────────────
init_db()

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Local AI Agent Server",
    description="A multi-agent AI assistant running locally.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Agents ───────────────────────────────────────────────────────────
AgentRegistry.register(GoogleExplainerAgent())
AgentRegistry.register(SummarizerAgent())
AgentRegistry.register(TranslatorAgent())
AgentRegistry.register(TaskAgent())
AgentRegistry.register(CoordinatorAgent())


# ── Pydantic Models ───────────────────────────────────────────────────────────
class ExplainRequest(BaseModel):
    text: str
    style: str = "simple"
    history: list = []

class SummarizeRequest(BaseModel):
    text: str
    length: str = "medium"  # short | medium | long

class TranslateRequest(BaseModel):
    text: str
    target_language: str = "english"

class ExecuteRequest(BaseModel):
    command: str

class TaskRequest(BaseModel):
    agent_name: str
    payload: dict

class TaskActionRequest(BaseModel):
    action: str            # add | list | complete | delete
    title: str = ""        # for add
    task_id: int = None    # for complete | delete
    filter: str = "all"    # for list: all | pending | done

class ChatRequest(BaseModel):
    text: str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {
        "status": "running",
        "agents": AgentRegistry.list_agents(),
        "version": "2.0.0"
    }

@app.post("/execute")
async def execute_command(request: ExecuteRequest):
    """Main Agent: execute an offline command."""
    logger.info(f"Command received: {request.command}")
    try:
        task = {"target_agent": "MainAgent", "command": request.command}
        result = TaskRouter.route(task)
        log_interaction("MainAgent", request.command, str(result.get("result", "")))
        return result
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/explain")
async def explain_text(request: ExplainRequest):
    """GoogleExplainerAgent: explain selected text."""
    logger.info(f"Explain request ({request.style}): {len(request.text)} chars")
    task = {
        "target_agent": "GoogleExplainer",
        "action": "explain",
        "text": request.text,
        "style": request.style,
        "history": request.history,
    }
    result = TaskRouter.route(task)
    if result.get("status") == "success":
        log_interaction("GoogleExplainer",
                        request.text[:200],
                        result.get("explanation", "")[:200])
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@app.post("/summarize")
async def summarize_text(request: SummarizeRequest):
    """SummarizerAgent: summarize text into bullet points."""
    logger.info(f"Summarize request ({request.length}): {len(request.text)} chars")
    task = {
        "target_agent": "Summarizer",
        "text": request.text,
        "length": request.length,
    }
    result = TaskRouter.route(task)
    if result.get("status") == "success":
        log_interaction("Summarizer", request.text[:200], result.get("summary", "")[:200])
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@app.post("/translate")
async def translate_text(request: TranslateRequest):
    """TranslatorAgent: translate text to a target language."""
    logger.info(f"Translate request -> {request.target_language}: {len(request.text)} chars")
    task = {
        "target_agent": "Translator",
        "text": request.text,
        "target_language": request.target_language,
    }
    result = TaskRouter.route(task)
    if result.get("status") == "success":
        log_interaction("Translator", request.text[:200], result.get("translation", "")[:200])
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@app.get("/translate/languages")
async def get_supported_languages():
    """Get the list of supported translation languages."""
    return {"languages": [{"key": k, "name": v} for k, v in SUPPORTED_LANGUAGES.items()]}

@app.post("/tasks")
async def manage_tasks(request: TaskActionRequest):
    """TaskAgent: manage a persistent to-do list."""
    task = {
        "target_agent": "TaskAgent",
        "action": request.action,
        "title": request.title,
        "task_id": request.task_id,
        "filter": request.filter,
    }
    result = TaskRouter.route(task)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@app.post("/task")
async def submit_generic_task(request: TaskRequest):
    """Generic task submission for any registered agent."""
    task = {"target_agent": request.agent_name, **request.payload}
    return TaskRouter.route(task)

@app.get("/history")
async def get_agent_history(agent: str = None, limit: int = 10):
    """Get interaction history, optionally filtered by agent name."""
    return {"history": get_history(agent, limit=limit)}

@app.post("/chat")
async def chat_with_coordinator(request: ChatRequest):
    """CoordinatorAgent: Uses Gemini Function Calling to autonomously use tools and satisfy complex requests."""
    logger.info(f"Chat request to Coordinator: {request.text[:100]}")
    task = {
        "target_agent": "Coordinator",
        "text": request.text
    }
    result = TaskRouter.route(task)
    if result.get("status") == "success":
        log_interaction("Coordinator", request.text[:200], result.get("response", "")[:200])
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result


if __name__ == "__main__":
    uvicorn.run(app, host=config.HOST, port=config.PORT)
