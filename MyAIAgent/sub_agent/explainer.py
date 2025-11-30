import os
import google.generativeai as genai
from typing import Dict, Any
from main_agent.core import AgentBase

class GoogleExplainerAgent(AgentBase):
    def __init__(self):
        super().__init__(name="GoogleExplainer", description="Explains text using Gemini")
        # Configure Gemini
        # User provided key directly
        api_key = "YOUR_API_KEY" 
        
        if not api_key or api_key == "YOUR_API_KEY_HERE":
             api_key = os.getenv("GOOGLE_API_KEY")

        if api_key:
            # Ensure env var is set for the library
            os.environ["GOOGLE_API_KEY"] = api_key
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
            self.logger.warning("GOOGLE_API_KEY not found. Explainer will run in mock mode.")

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action")
        if action == "explain":
            return self._explain(task.get("text", ""))
        return {"status": "error", "message": f"Unknown action: {action}"}

    def _explain(self, text: str) -> Dict[str, Any]:
        if not text:
            return {"status": "error", "message": "No text provided"}

        if not self.model:
            return {
                "status": "success",
                "explanation": f"[MOCK] Gemini is offline. Selected text: {text[:50]}..."
            }

        try:
            prompt = f"Explain the following text in simple, beginner-friendly language:\n\n{text}"
            response = self.model.generate_content(prompt)
            return {"status": "success", "explanation": response.text}
        except Exception as e:
            self.logger.error(f"Gemini API Error: {e}")
            return {"status": "error", "message": str(e)}
