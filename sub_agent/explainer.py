import os
import sys
import logging
from typing import Dict, Any

# Ensure project root is on path before any local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

import litellm
from main_agent.core import AgentBase

logger = logging.getLogger("GoogleExplainerAgent")

class GoogleExplainerAgent(AgentBase):
    def __init__(self):
        super().__init__(name="GoogleExplainer", description="Explains text flexibly using litellm")
        self.model = config.LLM_MODEL
        self.logger.info(f"Explainer initialized with model: {self.model}")

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action")
        if action == "explain":
            return self._explain(
                task.get("text", ""),
                task.get("style", "simple"),
                task.get("history", [])
            )
        return {"status": "error", "message": f"Unknown action: {action}"}

    def _explain(self, text: str, style: str = "simple", history: list = []) -> Dict[str, Any]:
        if not text:
            return {"status": "error", "message": "No text provided"}

        if not self.model:
            return {
                "status": "success",
                "explanation": f"[MOCK] LLM is offline. Style: {style}. Text: {text[:50]}..."
            }

        # Retry logic with exponential backoff
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                style_instructions = {
                    "simple": "Explain the following text in simple, beginner-friendly language:",
                    "textbook": "Provide a detailed, textbook-quality explanation. Include definitions, context, and examples where appropriate:",
                    "bullet": "Summarize the following text as a concise bullet-point list of key ideas:",
                    "translate": "Translate the following text to English (or explain it if already in English):"
                }
                style_instruction = style_instructions.get(style, style_instructions["simple"])

                context = ""
                if history:
                    context = "Conversation History:\n"
                    for msg in history:
                        role = "User" if msg.get("role") == "user" else "Agent"
                        context += f"{role}: {msg.get('content')}\n"
                    context += "\nCurrent Request:\n"

                prompt = f"{context}{style_instruction}\n\n{text}"
                response = litellm.completion(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return {"status": "success", "explanation": response.choices[0].message.content}

            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    self.logger.warning(f"LiteLLM API error (attempt {attempt+1}), retrying in {wait}s: {e}")
                    time.sleep(wait)
                else:
                    self.logger.error(f"LiteLLM API failed after {max_retries} attempts: {e}")
                    return {"status": "error", "message": str(e)}
