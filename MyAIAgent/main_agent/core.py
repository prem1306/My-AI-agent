import logging
import uuid
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MainAgent")

class AgentBase(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, description: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"Agent.{name}")
    
    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task and return the result."""
        pass

class AgentRegistry:
    """Registry to manage available agents."""
    
    _agents: Dict[str, AgentBase] = {}

    @classmethod
    def register(cls, agent: AgentBase):
        cls._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")

    @classmethod
    def get_agent(cls, name: str) -> Optional[AgentBase]:
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls):
        return list(cls._agents.keys())

import re
import os
from .tools import FileTools, SystemTools

class OfflineParser:
    """Parses natural language commands into system actions."""
    
    @staticmethod
    def parse_and_execute(command: str) -> str:
        command = command.strip().lower()
        
        # 1. Open Application
        # Pattern: open [app_name]
        match = re.match(r"open\s+(.+)", command)
        if match:
            app_name = match.group(1).strip()
            
            # Special case: open folder [path]
            if app_name.startswith("folder "):
                path = app_name[7:].strip()
                if not os.path.isabs(path):
                    path = os.path.join("sandbox", path)
                # Use explorer to open folder
                return SystemTools.run_shell_command(f"explorer \"{path}\"")

            # Basic mapping for common apps
            if "notepad" in app_name:
                return SystemTools.open_application("notepad")
            if "calc" in app_name:
                return SystemTools.open_application("calc")
            if "explorer" in app_name:
                return SystemTools.open_application("explorer")
            return f"Unknown app '{app_name}'. Try 'notepad', 'calc', 'explorer', or 'open folder [name]'."

        # 2. Create Folder
        # Pattern: create folder [path]
        match = re.match(r"create folder\s+(.+)", command)
        if match:
            path = match.group(1)
            # Sanitize path - simple check to ensure it's relative to sandbox or absolute
            # For this demo, we'll prefix with sandbox if it's a simple name
            if not os.path.isabs(path):
                path = os.path.join("sandbox", path)
            return FileTools.safe_write(path + "/.keep", "") # Create dir by writing a dummy file

        # 3. Delete Folder
        # Pattern: delete folder [path]
        match = re.match(r"delete folder\s+(.+)", command)
        if match:
            path = match.group(1)
            if not os.path.isabs(path):
                path = os.path.join("sandbox", path)
            return FileTools.safe_delete_folder(path)

        # 4. Run Shell Command (Whitelisted)
        # Pattern: run [cmd]
        match = re.match(r"run\s+(.+)", command)
        if match:
            cmd = match.group(1)
            return SystemTools.run_shell_command(cmd)

        # 5. History Command
        # Pattern: history
        if command == "history":
            from .database import get_history
            rows = get_history("MainAgent", limit=5)
            if not rows:
                return "No history found."
            
            history_str = "Recent Commands:\n"
            for row in rows:
                history_str += f"- {row['input_text']} ({row['timestamp']})\n"
            return history_str

        return "Command not recognized. Try 'open notepad', 'create folder foo', 'run dir', or 'history'."

class TaskRouter:
    """Routes tasks to the appropriate agent."""
    
    @staticmethod
    def route(task: Dict[str, Any]) -> Dict[str, Any]:
        target_agent_name = task.get("target_agent")
        
        # Direct Command Execution (Main Agent)
        if target_agent_name == "MainAgent":
            command = task.get("command")
            result = OfflineParser.parse_and_execute(command)
            return {"status": "success", "result": result}
        
        if not target_agent_name:
            return {"status": "error", "message": "No target_agent specified"}
        
        agent = AgentRegistry.get_agent(target_agent_name)
        if not agent:
            return {"status": "error", "message": f"Agent '{target_agent_name}' not found"}
        
        try:
            logger.info(f"Routing task to {target_agent_name}")
            return agent.execute(task)
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {"status": "error", "message": str(e)}
