import os
import sys
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main_agent.core import AgentBase
from main_agent.database import add_task, list_tasks, complete_task, delete_task


class TaskAgent(AgentBase):
    """Manages a persistent task/note list stored in SQLite."""

    def __init__(self):
        super().__init__(name="TaskAgent", description="Manages a persistent to-do list")

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "")

        if action == "add":
            return self._add(task.get("title", ""))
        elif action == "list":
            return self._list(task.get("filter", "all"))  # all | pending | done
        elif action == "complete":
            return self._complete(task.get("task_id"))
        elif action == "delete":
            return self._delete(task.get("task_id"))
        else:
            return {"status": "error", "message": f"Unknown action: '{action}'. Use add/list/complete/delete."}

    def _add(self, title: str) -> Dict[str, Any]:
        if not title:
            return {"status": "error", "message": "Task title cannot be empty"}
        result = add_task(title)
        return {"status": "success", "message": f"Task added: '{title}'", "task": result}

    def _list(self, filter_by: str = "all") -> Dict[str, Any]:
        tasks = list_tasks()
        if filter_by == "pending":
            tasks = [t for t in tasks if not t["done"]]
        elif filter_by == "done":
            tasks = [t for t in tasks if t["done"]]
        return {"status": "success", "tasks": tasks, "count": len(tasks)}

    def _complete(self, task_id) -> Dict[str, Any]:
        if task_id is None:
            return {"status": "error", "message": "task_id is required"}
        ok = complete_task(int(task_id))
        if ok:
            return {"status": "success", "message": f"Task {task_id} marked as done."}
        return {"status": "error", "message": f"Failed to complete task {task_id}"}

    def _delete(self, task_id) -> Dict[str, Any]:
        if task_id is None:
            return {"status": "error", "message": "task_id is required"}
        ok = delete_task(int(task_id))
        if ok:
            return {"status": "success", "message": f"Task {task_id} deleted."}
        return {"status": "error", "message": f"Failed to delete task {task_id}"}
