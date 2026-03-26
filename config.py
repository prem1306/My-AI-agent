"""
Central configuration for MyAIAgent.
Loads settings from .env file via python-dotenv.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- API Keys ---
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

# --- Paths ---
SANDBOX_DIR: str = str(BASE_DIR / "sandbox")
SAFE_ZONE_DIR: str = str(BASE_DIR / "safe_zone")
DB_PATH: str = str(BASE_DIR / "history.db")
LOG_FILE: str = str(BASE_DIR / "agent_system.log")

# --- Server ---
HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8000"))

# --- LLM Provider Settings (LiteLLM) ---
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini/gemini-2.5-flash")

# LiteLLM expects GEMINI_API_KEY, so we alias it if GOOGLE_API_KEY is used
if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

# Any standard API keys will be automatically picked up by litellm
# via os.getenv("GROQ_API_KEY"), os.getenv("ANTHROPIC_API_KEY"), etc.
