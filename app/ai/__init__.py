from .openai_client import OpenAIClient
from .ollama_client import OllamaClient

def get_ai_provider(config):
    provider_type = config.get('ai', {}).get('provider', 'openai')
    if provider_type == 'ollama':
        return OllamaClient(config)
    else:
        return OpenAIClient(config)
