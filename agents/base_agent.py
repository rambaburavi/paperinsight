class BaseAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, input_data):
        raise NotImplementedError("Each agent must implement run()")
