import io
from scipy.io.wavfile import read # type: ignore
from .base import TTSProvider

class TypecastClient(TTSProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('typecast', {}).get('api_key', '')
        self.voice_id = config.get('typecast', {}).get('voice_id', '')

    def generate_audio(self, text):
        if not self.api_key or not self.voice_id:
            print("Typecast Error: API Key or Voice ID missing")
            return None, None

        try:
            from typecast.client import Typecast # type: ignore
            from typecast.models import TTSRequest # type: ignore
            
            cli = Typecast(api_key=self.api_key)
            tts_response = cli.text_to_speech(TTSRequest(
                text=text,
                voice_id=self.voice_id,
                model="ssfm-v21"
            ))
            
            # Convert raw bytes to numpy array using scipy
            samplerate, data = read(io.BytesIO(tts_response.audio_data))
            return samplerate, data
            
        except ImportError:
            print("Typecast SDK not installed. Please run: pip install typecast-python")
            return None, None
        except Exception as e:
            print(f"Typecast TTS Error: {e}")
            return None, None
