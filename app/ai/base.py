class AIProvider:
    def __init__(self, config):
        self.config = config

    def chat(self, messages):
        raise NotImplementedError("Chat method not implemented")
