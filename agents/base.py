# agents/base.py

# --- Dual-purpose logger ---
def log(msg, logs=None):
    print(msg, flush=True)
    if logs is not None:
        logs.append(msg)

# --- Base agent class ---
class BaseAgent:
    def __init__(self, name, llm):
        self.name = name
        self.llm = llm

    def run(self, input_data):
        raise NotImplementedError("Subclasses must implement the run() method.")
