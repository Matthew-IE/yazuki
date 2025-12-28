import httpx # type: ignore
from .base import AIProvider

class OllamaClient(AIProvider):
    def __init__(self, config):
        super().__init__(config)
        self.model = config.get('ai', {}).get('ollama_model', 'llama3')
        self.endpoint = config.get('ai', {}).get('ollama_endpoint', 'http://localhost:11434/api/chat')

    def chat(self, messages):
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            # Use a generous timeout for local LLMs
            response = httpx.post(self.endpoint, json=payload, timeout=60.0)
            response.raise_for_status()
            result = response.json()
            return result.get('message', {}).get('content', '')
        except Exception as e:
            return f"Ollama Error: {str(e)}"
