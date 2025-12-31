from .typecast_client import TypecastClient
from .gpt_sovits_client import GPTSovitsClient

def get_tts_provider(config):
    # Check if TTS is enabled globally
    # Check 'tts' -> 'enabled' first, fallback to 'typecast' -> 'enabled' for legacy
    tts_enabled = config.get('tts', {}).get('enabled', False) or config.get('typecast', {}).get('enabled', False)
    
    if not tts_enabled:
        return None

    provider_type = config.get('tts', {}).get('provider', 'gpt_sovits')
    
    if provider_type == 'typecast':
        return TypecastClient(config)
    else:
        return GPTSovitsClient(config)
