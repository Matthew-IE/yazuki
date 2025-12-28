import os
import threading
import queue
import io
import numpy as np # type: ignore
import sounddevice as sd # type: ignore
from scipy.io.wavfile import write, read # type: ignore
from openai import OpenAI # type: ignore

class AIManager:
    def __init__(self, config):
        self.config = config
        self.recording = False
        self.audio_data = []
        self.samplerate = 44100
        self.client = None
        self.history = []
        self.system_prompt = "You are a helpful desktop companion named Yazuki. Keep your responses concise (under 20 words if possible) and friendly. Do not use markdown formatting."
        self.memory_enabled = config.get('ai', {}).get('memory_enabled', True)
        self.clear_memory()
        self.setup_client()
        
    def set_memory_enabled(self, enabled):
        self.memory_enabled = enabled
        print(f"Memory enabled: {enabled}")

    def clear_memory(self):
        self.history = [{"role": "system", "content": self.system_prompt}]
        print("Memory cleared.")

    def setup_client(self):
        api_key = self.config.get('ai', {}).get('api_key', '')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

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

    def stop_recording_and_process(self, callback):
        if not self.recording: return
        self.recording = False
        self.record_thread.join()
        print("Recording stopped.")
        
        if not self.audio_data:
            callback("Error: No audio recorded")
            return

        # Process in a separate thread to not block UI
        process_thread = threading.Thread(target=self._process_audio, args=(callback,))
        process_thread.start()

    def _process_audio(self, callback):
        if not self.client:
            callback("Error: No API Key configured")
            return

        try:
            # Save to temp file
            recording = np.concatenate(self.audio_data, axis=0)
            filename = "temp_input.wav"
            # Normalize
            recording = np.int16(recording * 32767)
            write(filename, self.samplerate, recording)
            
            print("Transcribing...")
            # Transcribe
            with open(filename, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            user_text = transcript.text
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
            response = self.client.chat.completions.create(
                model="gpt-5-nano", 
                messages=messages_to_send
            )
            reply = response.choices[0].message.content
            
            if self.memory_enabled:
                # Append AI reply to history
                self.history.append({"role": "assistant", "content": reply})
            
            print(f"AI replied: {reply}")
            callback(reply)
            
            # TTS (Typecast)
            if self.config.get('typecast', {}).get('enabled', False):
                try:
                    from typecast.client import Typecast
                    from typecast.models import TTSRequest
                    
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
                        sd.play(data, samplerate)
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
