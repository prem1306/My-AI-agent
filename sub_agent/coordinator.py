import os
import sys
import logging
import json
import litellm
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from main_agent.core import AgentBase, TaskRouter
from main_agent.database import search_history

logger = logging.getLogger("CoordinatorAgent")

# ── Tool Definitions for Gemini Function Calling ────────────────────────────
def ask_explainer(text: str, style: str = "simple") -> str:
    """Explains or deeply analyzes the given text. Use this when the user wants to understand something, translate something to English, or needs a textbook breakdown.
    Args:
        text: The text or concept to explain.
        style: The style of the explanation. Must be 'simple', 'textbook', or 'translate'. Default is 'simple'.
    """
    task = {
        "target_agent": "GoogleExplainer",
        "action": "explain",
        "text": text,
        "style": style,
        "history": []
    }
    result = TaskRouter.route(task)
    return result.get("explanation", result.get("message", "Error"))


def ask_summarizer(text: str, length: str = "medium") -> str:
    """Summarizes the given text into concise bullet points.
    Args:
        text: The text to summarize.
        length: The length of the summary. Must be 'short', 'medium', or 'long'. Default is 'medium'.
    """
    task = {
        "target_agent": "Summarizer",
        "text": text,
        "length": length
    }
    result = TaskRouter.route(task)
    return result.get("summary", result.get("message", "Error"))


def ask_translator(text: str, target_language: str) -> str:
    """Translates the given text into the target language.
    Args:
        text: The text to translate.
        target_language: The language to translate to (e.g., 'spanish', 'french', 'japanese').
    """
    task = {
        "target_agent": "Translator",
        "text": text,
        "target_language": target_language
    }
    result = TaskRouter.route(task)
    return result.get("translation", result.get("message", "Error"))


def manage_task(action: str, title: str = "", task_id: int = 0) -> str:
    """Manages the user's persistent to-do list. Use this when the user asks to save a note, add a task, remember something, complete a task, or list tasks.
    Args:
        action: Must be 'add', 'list', 'complete', or 'delete'.
        title: The text of the task (only needed for 'add').
        task_id: The ID of the task (only needed for 'complete' or 'delete').
    """
    task = {
        "target_agent": "TaskAgent",
        "action": action,
        "title": title,
        "task_id": task_id if task_id > 0 else None,
        "filter": "all"
    }
    result = TaskRouter.route(task)
    if action == "add":
        return f"Task added with ID {result.get('task_id')}: {result.get('task', {}).get('title')}"
    elif action == "list":
        tasks = result.get('tasks', [])
        if not tasks: return "No tasks found."
        return "\n".join([f"[{t['id']}] {t['title']} (Done: {bool(t['completed'])})" for t in tasks])
    else:
        return result.get("message", "Success")

def search_memory(keyword: str) -> str:
    """Searches the user's past interactions with the AI (explanations, translations, summaries). Use this when the user asks 'what did we talk about regarding [topic]', 'do you remember [topic]', or needs context from a previous chat.
    Args:
        keyword: The topic to search for in past interactions.
    """
    results = search_history(keyword, limit=5)
    if not results:
        return f"No past interactions found regarding '{keyword}'."
    
    formatted_results = []
    for r in results:
        agent = r.get("agent_type", "Unknown Agent")
        user_input = r.get("input_text", "")
        ai_reply = r.get("output_text", "")
        date = r.get("timestamp", "")
        formatted_results.append(f"[{date}] [Used {agent}]: User asked: '{user_input[:100]}...', AI replied: '{ai_reply[:200]}...'")
        
    return "\n\n".join(formatted_results)

def read_local_file(path: str) -> str:
    """Reads the text content of a local file. Use this when the user asks you to summarize, explain, or check a specific file on their computer.
    Args:
        path: The absolute path to the file.
    """
    try:
        path = os.path.normpath(path)
        if not os.path.exists(path):
            return f"Error: File not found at {path}"
        if not os.path.isfile(path):
            return f"Error: Path is a directory, not a file: {path}"
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(15000) # Read up to 15k chars to prevent token overflow
            
        if len(content) == 15000:
            return content + "\n...[TRUNCATED]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"

def list_local_directory(path: str) -> str:
    """Lists all files and folders in a local directory. Use this when the user asks what is inside a folder.
    Args:
        path: The absolute path to the directory.
    """
    try:
        path = os.path.normpath(path)
        if not os.path.exists(path):
            return f"Error: Directory not found at {path}"
        if not os.path.isdir(path):
            return f"Error: Path is a file, not a directory: {path}"
            
        items = os.listdir(path)
        if not items:
            return "Directory is empty."
            
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {e}"

# ── Universal Tool Schema (OpenAI format, converted by LiteLLM) ───────────
COORDINATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ask_explainer",
            "description": "Explains or deeply analyzes the given text. Use this when the user wants to understand something, translate something to English, or needs a textbook breakdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text or concept to explain."},
                    "style": {"type": "string", "description": "The style of the explanation ('simple', 'textbook', or 'translate')."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_summarizer",
            "description": "Summarizes the given text into concise bullet points.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to summarize."},
                    "length": {"type": "string", "description": "The length of the summary ('short', 'medium', 'long')."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_translator",
            "description": "Translates the given text into the target language.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to translate."},
                    "target_language": {"type": "string", "description": "The language to translate to (e.g., 'spanish')."}
                },
                "required": ["text", "target_language"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_task",
            "description": "Manages the user's persistent to-do list. Use this when the user asks to save a note, add a task, remember something, complete a task, or list tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Must be 'add', 'list', 'complete', or 'delete'."},
                    "title": {"type": "string", "description": "The text of the task (only needed for 'add')."},
                    "task_id": {"type": "integer", "description": "The ID of the task (only needed for 'complete' or 'delete')."}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Searches the user's past interactions with the AI (explanations, translations, summaries). Use this when the user asks 'what did we talk about regarding [topic]', 'do you remember [topic]', or needs context from a previous chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "The topic to search for in past interactions."}
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_local_file",
            "description": "Reads the text content of a local file on the user's computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The absolute path to the file to read."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_local_directory",
            "description": "Lists all files and folders in a local directory on the user's computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The absolute path to the folder to list."}
                },
                "required": ["path"]
            }
        }
    }
]

# ── Coordinator Agent ────────────────────────────────────────────────────────
class CoordinatorAgent(AgentBase):
    """An autonomous agent router that uses LiteLLM Function Calling to orchestrate sub-agents."""
    
    def __init__(self):
        super().__init__(name="Coordinator", description="Orchestrates sub-agents using universal function calling")
        self.model = config.LLM_MODEL
        self.available_functions = {
            "ask_explainer": ask_explainer,
            "ask_summarizer": ask_summarizer,
            "ask_translator": ask_translator,
            "manage_task": manage_task,
            "search_memory": search_memory,
            "read_local_file": read_local_file,
            "list_local_directory": list_local_directory
        }

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        user_input = task.get("text", "")
        if not user_input:
            return {"status": "error", "message": "No text provided to Coordinator"}
            
        return self._chat(user_input)

    def _chat(self, user_input: str) -> Dict[str, Any]:
        self.logger.info(f"Coordinator analyzing input via {self.model}: {user_input[:100]}")
        
        system_prompt = (
            "You are the MyAIAgent Coordinator. You have access to specialized tools (explainer, summarizer, translator, task_manager). "
            "The user will give you a request. You should use the appropriate tools to fulfill it. "
            "If the user asks for multiple things (e.g. 'translate this and save it as a task'), you must call BOTH tools. "
            "After using the tools, provide a friendly, unified response to the user summarizing what you did."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        try:
            # Recreate automatic function calling loop natively
            for attempt in range(5):
                response = litellm.completion(
                    model=self.model,
                    messages=messages,
                    tools=COORDINATOR_TOOLS
                )
                
                msg = response.choices[0].message
                
                if not msg.tool_calls:
                    # AI is done calling tools and gave a text response
                    return {"status": "success", "response": msg.content or "Done."}
                    
                # Append the AI's tool request to history
                # litellm returns an object, we need to convert it to a dict for the next API call sometimes,
                # but litellm handles passing the object back directly in most cases.
                messages.append(msg)
                
                # Execute each requested tool
                for tool_call in msg.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    
                    self.logger.info(f"Coordinator invoking tool: {func_name} with args {func_args}")
                    
                    if func_name in self.available_functions:
                        try:
                            result = self.available_functions[func_name](**func_args)
                        except Exception as e:
                            result = f"Error executing {func_name}: {e}"
                    else:
                        result = f"Error: Tool {func_name} not found."
                        
                    # Feed the result back to the AI
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": str(result)
                    })
                    
            return {"status": "error", "message": "Coordinator exceeded maximum tool iterations (5)."}
            
        except Exception as e:
            self.logger.error(f"Coordinator error: {e}")
            return {"status": "error", "message": str(e)}
