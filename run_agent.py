import uvicorn
import os
import sys
from pathlib import Path

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).parent))
import config

def main():
    print("=" * 50)
    print("  MyAIAgent — Local AI Agent System v2.0")
    print("=" * 50)
    print(f"  Server  : http://{config.HOST}:{config.PORT}")
    print(f"  API Docs: http://{config.HOST}:{config.PORT}/docs")
    print(f"  Model   : {config.GEMINI_MODEL}")
    print(f"  API Key : {'✓ Configured' if config.GOOGLE_API_KEY else '✗ NOT SET (mock mode)'}")
    print("-" * 50)
    print("  Agents  : GoogleExplainer | Summarizer | Translator | TaskAgent")
    print("-" * 50)
    print("  Press Ctrl+C to stop.\n")

    # Ensure sandbox and safe_zone directories exist
    os.makedirs(config.SANDBOX_DIR, exist_ok=True)
    os.makedirs(config.SAFE_ZONE_DIR, exist_ok=True)

    uvicorn.run(
        "main_agent.server:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
