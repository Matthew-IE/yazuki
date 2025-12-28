from openai import OpenAI # type: ignore
from .base import AIProvider

class OpenAIClient(AIProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('ai', {}).get('api_key', '')
        self.model = config.get('ai', {}).get('openai_model', 'gpt-4o-mini')
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def chat(self, messages):
        if not self.client:
            return "Error: OpenAI API Key not configured."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI Error: {str(e)}"
