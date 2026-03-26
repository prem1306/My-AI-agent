import sqlite3
import json
import logging
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger("Database")

DB_PATH = config.DB_PATH


def init_db():
    """Initialize all database tables."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Interaction history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT,
                input_text TEXT,
                output_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Task/note storage for TaskAgent
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


def log_interaction(agent_type: str, input_text: str, output_text: str):
    """Log an interaction to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO history (agent_type, input_text, output_text)
            VALUES (?, ?, ?)
        ''', (agent_type, input_text, output_text))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log interaction: {e}")


def get_history(agent_type: str = None, limit: int = 10):
    """Retrieve recent history, optionally filtered by agent type."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if agent_type:
            cursor.execute('''
                SELECT * FROM history
                WHERE agent_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (agent_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM history
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}")
        return []

def search_history(query: str, limit: int = 5) -> list:
    """Search interaction history using a keyword."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT * FROM history
            WHERE input_text LIKE ? OR output_text LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (search_term, search_term, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Failed to search history: {e}")
        return []


# --- Task CRUD for TaskAgent ---
def add_task(title: str) -> dict:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        return {"id": task_id, "title": title, "done": False}
    except Exception as e:
        logger.error(f"Failed to add task: {e}")
        return {}


def list_tasks() -> list:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        return []


def complete_task(task_id: int) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        return False


def delete_task(task_id: int) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to delete task: {e}")
        return False
