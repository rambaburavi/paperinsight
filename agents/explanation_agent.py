class ExplanationAgent:
    def __init__(self, llm, level="beginner"):
        self.llm = llm
        self.level = level

    def run(self, overview, contributions, limitations):
        prompt = f"""
You are producing a final decision summary for a research paper.

Audience level: {self.level}

Based on:
- Paper overview
- Extracted contributions
- Identified limitations

Tasks:
- Judge reliability realistically
- State confidence level
- Give practical guidance
- NEVER leave sections empty

Return STRICT JSON ONLY:

{{
  "reliability": "",
  "confidence_level": "",
  "when_to_use": [],
  "when_not_to_use": [],
  "future_scope": ""
}}

Overview:
{overview}

Contributions:
{contributions}

Limitations:
{limitations}
"""
        return self.llm(prompt)
