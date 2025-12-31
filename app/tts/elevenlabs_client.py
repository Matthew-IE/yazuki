import io
import numpy as np # type: ignore
from elevenlabs.client import ElevenLabs # type: ignore
from elevenlabs import VoiceSettings # type: ignore
from .base import TTSProvider
import soundfile as sf # type: ignore

class ElevenLabsClient(TTSProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('elevenlabs', {}).get('api_key', '')
        self.voice_id = config.get('elevenlabs', {}).get('voice_id', '')
        self.model_id = config.get('elevenlabs', {}).get('model_id', 'eleven_flash_v2_5')
        
        # Voice Settings
        self.stability = config.get('elevenlabs', {}).get('stability', 0.5)
        self.similarity_boost = config.get('elevenlabs', {}).get('similarity_boost', 0.75)
        self.style = config.get('elevenlabs', {}).get('style', 0.0)
        self.use_speaker_boost = config.get('elevenlabs', {}).get('use_speaker_boost', True)
        
        self.client = None

    def _get_client(self):
        if self.client is None and self.api_key:
            try:
                self.client = ElevenLabs(api_key=self.api_key)
            except Exception as e:
                print(f"Failed to initialize ElevenLabs client: {e}")
                return None
        return self.client

    def generate_audio(self, text):
        client = self._get_client()
        if not client:
            print("ElevenLabs client not initialized (missing API key?)")
            return None, None

        if not self.voice_id:
            print("ElevenLabs Error: No Voice ID specified")
            return None, None

        try:
            # Generate audio
            audio_generator = client.text_to_speech.convert(
                voice_id=self.voice_id,
                optimize_streaming_latency="0",
                output_format="mp3_44100_128",
                text=text,
                model_id=self.model_id,
                voice_settings=VoiceSettings(
                    stability=self.stability,
                    similarity_boost=self.similarity_boost,
                    style=self.style,
                    use_speaker_boost=self.use_speaker_boost,
                ),
            )

            # Consume generator to get full bytes
            audio_bytes = b"".join(audio_generator)
            
            # Convert to numpy array using soundfile
            # soundfile can read from a bytes-like object if wrapped in BytesIO
            with io.BytesIO(audio_bytes) as f:
                data, samplerate = sf.read(f)
            
            # Ensure float32
            if data.dtype != np.float32:
                data = data.astype(np.float32)

            return samplerate, data

        except Exception as e:
            print(f"ElevenLabs Generation Error: {e}")
            return None, None
