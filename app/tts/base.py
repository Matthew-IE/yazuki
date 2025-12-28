class TTSProvider:
    def __init__(self, config):
        self.config = config

    def generate_audio(self, text):
        """
        Generates audio from text.
        Returns: (samplerate, audio_data_numpy_array)
        """
        raise NotImplementedError("generate_audio method not implemented")
