class ContributionExtractionAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, chunks):
        MAX_CHARS = 3500
        text = ""
        for c in chunks:
            if c.get("text", "").strip():
                if len(text) + len(c["text"]) < MAX_CHARS:
                    text += c["text"] + "\n\n"
                else:
                    break

        prompt = f"""
You are extracting key contributions and experimental performance results from a research paper.

STRICT RULES:

1. Extract ONLY explicitly reported experimental performance results.
2. Extract ONLY numeric values (Accuracy, AUC, F1-score, Precision, Recall, etc.).
3. Do NOT infer metrics.
4. Do NOT fabricate numbers.
5. If multiple values exist for the same metric, include all explicitly reported final model values.
6. Ignore comparison tables unless clearly stated as final model performance.
7. If no numeric results are reported, return an empty performance_summary list.

Max 3 primary contributions.
Max 3 secondary contributions.
Max 5 performance metrics.

Return STRICT JSON ONLY (no markdown, no explanation).

JSON format:
{{
  "primary_contributions": [],
  "secondary_contributions": [],
  "performance_summary": [
    {{
      "metric": "Accuracy",
      "value": "98.4%"
    }}
  ]
}}

Paper text:
{text}
"""



        return self.llm(prompt)
