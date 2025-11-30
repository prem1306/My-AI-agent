import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger("Database")

DB_PATH = "history.db"

def init_db():
    """Initialize the database table."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT,
                input_text TEXT,
                output_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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

def get_history(agent_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
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
