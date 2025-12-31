from .typecast_client import TypecastClient
from .gpt_sovits_client import GPTSovitsClient
from .elevenlabs_client import ElevenLabsClient

def get_tts_provider(config):
    # Check if TTS is enabled globally
    # Check 'tts' -> 'enabled' first, fallback to 'typecast' -> 'enabled' for legacy
    tts_enabled = config.get('tts', {}).get('enabled', False) or config.get('typecast', {}).get('enabled', False)
    
    if not tts_enabled:
        return None

    provider_type = config.get('tts', {}).get('provider', 'gpt_sovits')
    
    if provider_type == 'typecast':
        return TypecastClient(config)
    elif provider_type == 'elevenlabs':
        return ElevenLabsClient(config)
    else:
        return GPTSovitsClient(config)
