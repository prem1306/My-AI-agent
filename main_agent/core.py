import logging
import uuid
import re
import os
import sys
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
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

    @classmethod
    def describe_agents(cls) -> list:
        return [{"name": a.name, "description": a.description} for a in cls._agents.values()]


from .tools import FileTools, SystemTools


class OfflineParser:
    """Parses natural language commands into system actions."""

    HELP_TEXT = (
        "Available commands:\n"
        "  open <app>          - Open notepad, calc, or explorer\n"
        "  open folder <path>  - Open a folder in Explorer\n"
        "  create folder <n>   - Create a folder in sandbox\n"
        "  delete folder <n>   - Delete a folder from sandbox\n"
        "  list sandbox        - List sandbox contents\n"
        "  run <cmd>           - Run a whitelisted shell command\n"
        "  history             - Show recent command history\n"
        "  agents              - List all registered agents\n"
        "  help                - Show this help message"
    )

    @staticmethod
    def parse_and_execute(command: str) -> str:
        cmd = command.strip().lower()

        # help
        if cmd == "help":
            return OfflineParser.HELP_TEXT

        # agents
        if cmd == "agents":
            agents = AgentRegistry.describe_agents()
            if not agents:
                return "No agents registered."
            return "Registered Agents:\n" + "\n".join(
                f"  • {a['name']}: {a['description']}" for a in agents
            )

        # open folder <path>
        m = re.match(r"open folder\s+(.+)", cmd)
        if m:
            path = m.group(1).strip()
            if not os.path.isabs(path):
                path = os.path.join(config.SANDBOX_DIR, path)
            return SystemTools.run_shell_command(f'explorer "{path}"')

        # open <app>
        m = re.match(r"open\s+(\w+)$", cmd)
        if m:
            app = m.group(1)
            return SystemTools.open_application(app)

        # create folder <name>
        m = re.match(r"create folder\s+(.+)", cmd)
        if m:
            path = m.group(1).strip()
            if not os.path.isabs(path):
                path = os.path.join(config.SANDBOX_DIR, path)
            return FileTools.safe_write(path + "/.keep", "")

        # delete folder <name>
        m = re.match(r"delete folder\s+(.+)", cmd)
        if m:
            path = m.group(1).strip()
            if not os.path.isabs(path):
                path = os.path.join(config.SANDBOX_DIR, path)
            return FileTools.safe_delete_folder(path)

        # list sandbox
        if cmd == "list sandbox":
            return FileTools.list_sandbox()

        # run <cmd>
        m = re.match(r"run\s+(.+)", cmd)
        if m:
            return SystemTools.run_shell_command(m.group(1).strip())

        # history
        if cmd == "history":
            from .database import get_history
            rows = get_history("MainAgent", limit=5)
            if not rows:
                return "No history found."
            return "Recent Commands:\n" + "\n".join(
                f"  [{r['timestamp']}] {r['input_text']}" for r in rows
            )

        return f"Command not recognized: '{command}'. Type 'help' for available commands."


class TaskRouter:
    """Routes tasks to the appropriate agent."""

    @staticmethod
    def route(task: Dict[str, Any]) -> Dict[str, Any]:
        target_agent_name = task.get("target_agent")

        if target_agent_name == "MainAgent":
            command = task.get("command", "")
            result = OfflineParser.parse_and_execute(command)
            return {"status": "success", "result": result}

        if not target_agent_name:
            return {"status": "error", "message": "No target_agent specified"}

        agent = AgentRegistry.get_agent(target_agent_name)
        if not agent:
            return {
                "status": "error",
                "message": f"Agent '{target_agent_name}' not found. Available: {AgentRegistry.list_agents()}"
            }

        try:
            logger.info(f"Routing task to {target_agent_name}")
            return agent.execute(task)
        except Exception as e:
            logger.error(f"Error executing task on {target_agent_name}: {e}")
            return {"status": "error", "message": str(e)}
