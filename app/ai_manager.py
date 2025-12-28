import os
import threading
import queue
import io
import time
import numpy as np # type: ignore
import sounddevice as sd # type: ignore
from scipy.io.wavfile import write, read # type: ignore
from openai import OpenAI # type: ignore
from app.ai import get_ai_provider

class AIManager:
    def __init__(self, config):
        self.config = config
        self.recording = False
        self.audio_data = []
        self.samplerate = 44100
        self.client = None
        self.provider = None
        self.history = []
        self.system_prompt = "You are a helpful desktop companion named Yazuki. Keep your responses concise (under 20 words if possible) and friendly. Do not use markdown formatting."
        self.memory_enabled = config.get('ai', {}).get('memory_enabled', True)
        self.mouth_sensitivity = config.get('render', {}).get('mouth_sensitivity', 5.0)
        self.local_whisper_model = None
        self.clear_memory()
        self.setup_client()
        
    def set_mouth_sensitivity(self, value):
        self.mouth_sensitivity = value

    def set_memory_enabled(self, enabled):
        self.memory_enabled = enabled
        print(f"Memory enabled: {enabled}")

    def clear_memory(self):
        self.history = [{"role": "system", "content": self.system_prompt}]
        print("Memory cleared.")

    def setup_client(self):
        # Setup OpenAI Client for STT (if key exists)
        api_key = self.config.get('ai', {}).get('api_key', '')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
            
        # Setup Chat Provider
        self.provider = get_ai_provider(self.config)

    def get_input_devices(self):
        try:
            devices = sd.query_devices()
            input_devices = []
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    input_devices.append((i, dev['name']))
            return input_devices
        except Exception as e:
            print(f"Error listing devices: {e}")
            return []

    def start_recording(self):
        if self.recording: return
        self.recording = True
        self.audio_data = []
        
        # Start recording in a separate thread to not block UI
        self.record_thread = threading.Thread(target=self._record_loop)
        self.record_thread.start()
        print("Recording started...")

    def _record_loop(self):
        device_index = self.config.get('ai', {}).get('input_device', None)
        # If device_index is -1 or None, use default
        if device_index == -1: 
            device_index = None
            
        try:
            with sd.InputStream(samplerate=self.samplerate, channels=1, device=device_index, callback=self._audio_callback):
                while self.recording:
                    sd.sleep(100)
        except Exception as e:
            print(f"Recording error: {e}")
            self.recording = False

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.audio_data.append(indata.copy())

    def stop_recording_and_process(self, callback, lip_sync_callback=None):
        if not self.recording: return
        self.recording = False
        self.record_thread.join()
        print("Recording stopped.")
        
        if not self.audio_data:
            callback("Error: No audio recorded")
            return

        # Process in a separate thread to not block UI
        process_thread = threading.Thread(target=self._process_audio, args=(callback, lip_sync_callback))
        process_thread.start()

    def _process_audio(self, callback, lip_sync_callback=None):
        try:
            # Save to temp file
            recording = np.concatenate(self.audio_data, axis=0)
            filename = "temp_input.wav"
            # Normalize
            recording = np.int16(recording * 32767)
            write(filename, self.samplerate, recording)
            
            print("Transcribing...")
            user_text = ""
            
            # Transcribe
            if self.client:
                # Use OpenAI Whisper if available
                with open(filename, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file
                    )
                user_text = transcript.text
            else:
                # Fallback to local Whisper (openai-whisper)
                try:
                    import whisper # type: ignore
                    if self.local_whisper_model is None:
                        print("Loading local Whisper model (small)...")
                        self.local_whisper_model = whisper.load_model("small")
                    
                    result = self.local_whisper_model.transcribe(filename)
                    user_text = result["text"]
                except ImportError:
                    callback("Error: OpenAI Key missing and 'openai-whisper' not installed. Run: pip install openai-whisper")
                    return
                except Exception as e:
                    callback(f"STT Error: {e}")
                    return

            print(f"User said: {user_text}")
            
            if not user_text.strip():
                callback("...")
                return

            print("Sending to AI...")
            
            messages_to_send = []
            
            if self.memory_enabled:
                # Append user message to history
                self.history.append({"role": "user", "content": user_text})
                messages_to_send = self.history
            else:
                # Use fresh context
                messages_to_send = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_text}
                ]
            
            # Chat
            reply = self.provider.chat(messages_to_send)
            
            if self.memory_enabled:
                # Append AI reply to history
                self.history.append({"role": "assistant", "content": reply})
            
            print(f"AI replied: {reply}")
            callback(reply)
            
            # TTS (Typecast)
            if self.config.get('typecast', {}).get('enabled', False):
                try:
                    from typecast.client import Typecast # type: ignore
                    from typecast.models import TTSRequest # type: ignore
                    
                    tts_api_key = self.config.get('typecast', {}).get('api_key', '')
                    voice_id = self.config.get('typecast', {}).get('voice_id', '')
                    
                    if tts_api_key and voice_id:
                        print("Generating speech...")
                        cli = Typecast(api_key=tts_api_key)
                        tts_response = cli.text_to_speech(TTSRequest(
                            text=reply,
                            voice_id=voice_id,
                            model="ssfm-v21"
                        ))
                        
                        # Play audio
                        # Convert raw bytes to numpy array using scipy
                        samplerate, data = read(io.BytesIO(tts_response.audio_data))
                        
                        # Simple Lip Sync Loop
                        # We need to play audio and update lip sync value simultaneously
                        # Since sd.play is non-blocking, we can loop while it plays
                        
                        duration = len(data) / samplerate
                        start_time = time.time()
                        
                        sd.play(data, samplerate)
                        
                        while time.time() - start_time < duration:
                            # Calculate current amplitude for lip sync
                            # Get current position in samples
                            current_time = time.time() - start_time
                            sample_idx = int(current_time * samplerate)
                            
                            if sample_idx < len(data):
                                # Get a small chunk around current sample
                                chunk_size = 1024
                                start = max(0, sample_idx - chunk_size // 2)
                                end = min(len(data), sample_idx + chunk_size // 2)
                                chunk = data[start:end]
                                
                                if len(chunk) > 0:
                                    # Calculate RMS amplitude
                                    # Normalize to 0-1 range (assuming 16-bit audio)
                                    rms = np.sqrt(np.mean(chunk.astype(float)**2))
                                    amplitude = rms / 32768.0
                                    
                                    # Scale up a bit to make mouth open more visible
                                    lip_value = min(1.0, amplitude * self.mouth_sensitivity)
                                    
                                    if lip_sync_callback:
                                        lip_sync_callback(lip_value)
                            
                            time.sleep(0.016) # ~60fps update
                            
                        if lip_sync_callback:
                            lip_sync_callback(0.0) # Close mouth
                            
                        sd.wait()
                except ImportError:
                    print("Typecast SDK not installed. Please run: pip install typecast-python")
                except Exception as e:
                    print(f"TTS Error: {e}")
            
            # Cleanup
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            print(f"AI Error: {e}")
            callback(f"Error: {str(e)}")
