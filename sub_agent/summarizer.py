import os
import sys
import time
import litellm
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from main_agent.core import AgentBase


class SummarizerAgent(AgentBase):
    """Summarizes text into concise bullet points using litellm."""

    def __init__(self):
        super().__init__(name="Summarizer", description="Summarizes text into bullet points")
        self.model = config.LLM_MODEL

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        text = task.get("text", "")
        length = task.get("length", "medium")  # short | medium | long
        return self._summarize(text, length)

    def _summarize(self, text: str, length: str = "medium") -> Dict[str, Any]:
        if not text:
            return {"status": "error", "message": "No text provided"}

        if not self.model:
            return {"status": "success", "summary": f"[MOCK] Summary of: {text[:80]}..."}

        length_instructions = {
            "short": "in 3-5 bullet points",
            "medium": "in 5-8 bullet points",
            "long": "in 8-12 bullet points with sub-bullets where helpful"
        }
        length_hint = length_instructions.get(length, length_instructions["medium"])

        prompt = (
            f"Please summarize the following text {length_hint}. "
            f"Use clear, concise language. Start each bullet with '•'.\n\n{text}"
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return {"status": "success", "summary": response.choices[0].message.content}
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    self.logger.error(f"Summarizer failed: {e}")
                    return {"status": "error", "message": str(e)}
