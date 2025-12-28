from .typecast_client import TypecastClient
from .gpt_sovits_client import GPTSovitsClient

def get_tts_provider(config):
    provider_type = config.get('tts', {}).get('provider', 'typecast')
    
    # Backward compatibility check: if 'typecast' key exists and enabled is true, default to typecast
    if config.get('typecast', {}).get('enabled', False) and 'provider' not in config.get('tts', {}):
        return TypecastClient(config)
        
    if provider_type == 'gpt_sovits':
        return GPTSovitsClient(config)
    else:
        return TypecastClient(config)
