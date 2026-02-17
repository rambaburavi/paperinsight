class SectionUnderstandingAgent:
    def __init__(self, llm, section_name="Paper Overview"):
        self.llm = llm
        self.section_name = section_name

    def run(self, chunks):
        MAX_CHARS = 2500
        text = ""
        for c in chunks:
            if c.get("text", "").strip():
                if len(text) + len(c["text"]) < MAX_CHARS:
                    text += c["text"] + "\n\n"
                else:
                    break

        prompt = f"""
You are analyzing a research paper.

Task:
Create a clear "Paper at a Glance" summary.

Rules:
- Prefer explicit statements from the text
- If not explicitly stated, infer ONLY when the text strongly implies it
- Do NOT guess or add common research practices
- If inferred, prefix value with "Inferred:"
- Keep logical flow: problem → data → method → model → results → domain
- One concise sentence per field
- Return STRICT JSON ONLY

JSON format:
{{
  "problem": "",
  "dataset": "",
  "method": "",
  "model": "",
  "evaluation_metrics": "",
  "best_result": "",
  "application_domain": ""
}}

Paper text:
{text}
"""
        return self.llm(prompt)
