from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import logging
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_agent.core import AgentRegistry, TaskRouter
from sub_agent.explainer import GoogleExplainerAgent
from main_agent.database import init_db, log_interaction, get_history

from fastapi.middleware.cors import CORSMiddleware

# Initialize Logging
logger = logging.getLogger("AgentServer")

class ExplainRequest(BaseModel):
    text: str

class TaskRequest(BaseModel):
    agent_name: str
    payload: dict

class ExecuteRequest(BaseModel):
    command: str

# Initialize Database
init_db()

app = FastAPI(title="Local AI Agent Server")

# Allow CORS for Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Agents
explainer = GoogleExplainerAgent()
AgentRegistry.register(explainer)

@app.get("/health")
def health_check():
    return {"status": "running", "agents": AgentRegistry.list_agents()}

@app.post("/execute")
async def execute_command(request: ExecuteRequest):
    """Endpoint for Main Agent offline commands."""
    logger.info(f"Received command: {request.command}")
    
    try:
        task = {
            "target_agent": "MainAgent",
            "command": request.command
        }
        
        result = TaskRouter.route(task)
        
        # Log to database
        log_interaction("MainAgent", request.command, str(result.get("result", "")))
        
        return result
    except Exception as e:
        logger.error(f"Execution Error: {e}")
        return {"status": "error", "message": f"Server Error: {str(e)}"}

@app.post("/explain")
async def explain_text(request: ExplainRequest):
    """Endpoint for the Chrome Extension to call."""
    logger.info(f"Received explanation request for text length: {len(request.text)}")
    
    task = {
        "target_agent": "GoogleExplainer",
        "action": "explain",
        "text": request.text
    }
    
    result = TaskRouter.route(task)
    
    # Log to database
    if result.get("status") == "success":
        log_interaction("GoogleExplainer", request.text[:200] + "...", result.get("explanation", "")[:200] + "...")
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    
    return result

@app.post("/task")
async def submit_task(request: TaskRequest):
    """Generic task submission endpoint."""
    task = {
        "target_agent": request.agent_name,
        **request.payload
    }
    return TaskRouter.route(task)

@app.get("/history")
async def get_agent_history(agent: str = None):
    """Get interaction history."""
    return {"history": get_history(agent)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
