from openai import OpenAI # type: ignore
from .base import AIProvider

class OpenRouterClient(AIProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('ai', {}).get('openrouter_api_key', '')
        self.model = config.get('ai', {}).get('openrouter_model', 'openai/gpt-3.5-turbo')
        self.client = None
        if self.api_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )

    def chat(self, messages):
        if not self.client:
            return "Error: OpenRouter API Key not configured."
        
        try:
            # OpenRouter recommends sending HTTP-Referer and X-Title headers
            # The openai python client allows extra_headers
            extra_headers = {
                "HTTP-Referer": "https://github.com/Matthew-IE/yazuki",
                "X-Title": "Yazuki"
            }
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                extra_headers=extra_headers
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenRouter Error: {str(e)}"
