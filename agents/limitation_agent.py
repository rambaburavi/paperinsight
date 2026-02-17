class LimitationAssumptionAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, chunks):
        MAX_CHARS = 3500  # 🔥 SAFE LIMIT
        text = ""
        for c in chunks:
            if c.get("text", "").strip():
                if len(text) + len(c["text"]) < MAX_CHARS:
                    text += c["text"] + "\n\n"
                else:
                    break


        prompt = f"""
You are identifying limitations and risks in a research paper.

Rules:
- Prefer explicit limitations
- If none, infer conservatively
- NEVER say "Not reported"
- One sentence per item
- Return STRICT JSON ONLY

JSON format:
{{
  "data_limitations": [],
  "methodological_risks": [],
  "generalization_risks": [],
  "key_assumptions": []
}}

Paper text:
{text}
"""
        return self.llm(prompt)
