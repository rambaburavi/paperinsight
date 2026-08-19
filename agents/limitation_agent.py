class LimitationAssumptionAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, chunks):
        MAX_CHARS = 9000

        text_parts = []

        for c in chunks:
            text = c.get("text", "").strip()

            if text:
                text_parts.append(text)

        text = "\n\n".join(text_parts)

        if not text:
            return """
{
    "data_limitations": [],
    "methodological_risks": [],
    "generalization_risks": [],
    "key_assumptions": []
}
"""

        text = text[:MAX_CHARS]

        prompt = f"""
You are an expert research-paper analysis assistant.

Analyze the supplied research paper evidence and identify:

1. DATA LIMITATIONS
2. METHODOLOGICAL RISKS
3. GENERALIZATION RISKS
4. KEY ASSUMPTIONS

DATA LIMITATIONS:
Identify limitations related to datasets, retrieval sources,
sample size, language coverage, domain coverage, or data quality.

METHODOLOGICAL RISKS:
Identify limitations or risks related to the methodology,
experimental design, evaluation procedure, model design,
training procedure, or comparison setup.

GENERALIZATION RISKS:
Identify reasons why the reported findings may not generalize
to other datasets, languages, domains, models, or real-world settings.

KEY ASSUMPTIONS:
Identify important assumptions made by the authors or required
for the proposed approach to work.

IMPORTANT RULES:
- Use ONLY information supported by the supplied paper.
- Prefer limitations explicitly stated or clearly supported by
  the experimental setup.
- Do not invent generic limitations.
- Do not claim a limitation simply because something was not mentioned.
- Do not say "Not reported".
- Keep each item to one clear sentence.
- Maximum 4 items per category.
- Return STRICT JSON ONLY.
- No markdown.
- No explanation outside JSON.

JSON FORMAT:

{{
    "data_limitations": [],
    "methodological_risks": [],
    "generalization_risks": [],
    "key_assumptions": []
}}

PAPER EVIDENCE:

{text}
"""

        return self.llm(prompt)