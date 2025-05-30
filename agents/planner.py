# agents/planner.py

from .base import BaseAgent, log

class PlannerAgent(BaseAgent):
    def run(self, query, pdf_uploaded):
        if pdf_uploaded:
            return 3, "User uploaded a PDF. Using PDF chunking flow."
        prompt = (
            f"Given the user query: \"{query}\", pick a task pipeline from:\n"
            "1. Retrieve > Scrape > Synthesize\n"
            "2. Retrieve > Scrape > Evaluate > Synthesize\n"
            "3. Load PDF > Chunk > Synthesize\n"
            "Just return the flow number and a one-line reason."
        )
        response = self.llm(prompt) if self.llm else "2: Default to most robust pipeline."
        flow_number = 2
        reason = ""
        for line in response.splitlines():
            if line.strip() and line[0] in "123":
                flow_number = int(line[0])
                reason = line[2:].strip()
                break
        return flow_number, reason
