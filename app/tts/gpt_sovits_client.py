import io
import os
from scipy.io.wavfile import read # type: ignore
from .base import TTSProvider

class GPTSovitsClient(TTSProvider):
    def __init__(self, config):
        super().__init__(config)
        # Default to the port mentioned in the guide (9872) if not specified, 
        # but keep user config if they set it.
        self.endpoint = config.get('gpt_sovits', {}).get('endpoint', 'http://localhost:9872/')
        self.ref_audio_path = config.get('gpt_sovits', {}).get('ref_audio_path', '')
        self.prompt_text = config.get('gpt_sovits', {}).get('prompt_text', '')
        self.prompt_lang = config.get('gpt_sovits', {}).get('prompt_lang', 'English')
        self.text_lang = config.get('gpt_sovits', {}).get('text_lang', 'English')
        self.client = None

    def _get_client(self):
        if self.client is None:
            try:
                from gradio_client import Client, file # type: ignore
                self.client = Client(self.endpoint)
            except ImportError:
                print("gradio_client not installed. Run: pip install gradio_client")
                return None
            except Exception as e:
                print(f"Failed to connect to GPT-SoVITS at {self.endpoint}: {e}")
                return None
        return self.client

    def generate_audio(self, text):
        client = self._get_client()
        if not client:
            return None, None

        if not self.ref_audio_path or not os.path.exists(self.ref_audio_path):
            print(f"GPT-SoVITS Error: Reference audio not found at {self.ref_audio_path}")
            return None, None

        try:
            from gradio_client import file # type: ignore
            
            # Call /get_tts_wav as per the guide
            result_path = client.predict(
                ref_wav_path=file(self.ref_audio_path),
                prompt_text=self.prompt_text,
                prompt_language=self.prompt_lang,
                text=text,
                text_language=self.text_lang,
                how_to_cut="Slice by English punct",
                top_k=15,
                top_p=0.8,
                temperature=1,
                ref_free=False,
                speed=1,
                if_freeze=False,
                inp_refs=None,
                sample_steps="20",
                if_sr=False,
                pause_second=0.3,
                api_name="/get_tts_wav"
            )
            
            # Result is a filepath to the generated wav
            if result_path and os.path.exists(result_path):
                samplerate, data = read(result_path)
                return samplerate, data
            else:
                print("GPT-SoVITS Error: No output file returned")
                return None, None
            
        except Exception as e:
            print(f"GPT-SoVITS TTS Error: {e}")
            return None, None
