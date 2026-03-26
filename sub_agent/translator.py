import os
import sys
import time
import litellm
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from main_agent.core import AgentBase


# Supported target languages and their display names
SUPPORTED_LANGUAGES = {
    "english": "English",
    "spanish": "Spanish",
    "french": "French",
    "german": "German",
    "hindi": "Hindi",
    "japanese": "Japanese",
    "chinese": "Chinese (Simplified)",
    "arabic": "Arabic",
    "portuguese": "Portuguese",
    "russian": "Russian",
    "korean": "Korean",
    "italian": "Italian",
}


class TranslatorAgent(AgentBase):
    """Translates text to a target language using litellm."""

    def __init__(self):
        super().__init__(name="Translator", description="Translates text to a specified language")
        self.model = config.LLM_MODEL

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        text = task.get("text", "")
        target_language = task.get("target_language", "english").lower()
        return self._translate(text, target_language)

    def _translate(self, text: str, target_language: str) -> Dict[str, Any]:
        if not text:
            return {"status": "error", "message": "No text provided"}

        lang_display = SUPPORTED_LANGUAGES.get(
            target_language, target_language.capitalize()
        )

        if not self.model:
            return {
                "status": "success",
                "translation": f"[MOCK] Translation to {lang_display}: {text[:80]}...",
                "target_language": lang_display
            }

        prompt = (
            f"Translate the following text to {lang_display}. "
            f"Provide ONLY the translation, no explanations or extra text.\n\n{text}"
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return {
                    "status": "success",
                    "translation": response.choices[0].message.content,
                    "target_language": lang_display
                }
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    self.logger.error(f"Translator failed: {e}")
                    return {"status": "error", "message": str(e)}

    @staticmethod
    def supported_languages() -> list:
        return [{"key": k, "name": v} for k, v in SUPPORTED_LANGUAGES.items()]
