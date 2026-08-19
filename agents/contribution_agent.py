class ContributionExtractionAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, chunks):
        MAX_CHARS = 12000

        text_parts = []

        for c in chunks:
            text = c.get("text", "").strip()

            if text:
                text_parts.append(text)

        text = "\n\n".join(text_parts)

        if not text:
            return """
{
    "primary_contributions": [],
    "secondary_contributions": [],
    "performance_summary": []
}
"""

        text = text[:MAX_CHARS]

        prompt = f"""
You are an expert research-paper analysis assistant.

Analyze the supplied research paper evidence and extract:

1. PRIMARY CONTRIBUTIONS
2. SECONDARY CONTRIBUTIONS
3. PERFORMANCE SUMMARY

PRIMARY CONTRIBUTIONS:
Identify the most important things the paper introduces, proposes,
demonstrates, or achieves.

SECONDARY CONTRIBUTIONS:
Identify additional useful contributions, observations, comparisons,
or improvements made by the paper.

PERFORMANCE SUMMARY:
Extract important experimentally reported results from the paper.

For performance:
- Include only values actually reported in the paper.
- Include metric names and values when available.
- Include benchmark/task names when they help explain the result.
- Do not invent numbers.
- Do not calculate values that are not reported.
- If the paper reports qualitative improvements without numeric values,
  you may describe those improvements briefly.
- Do not assume that a higher number is automatically better.
- Preserve the meaning of the reported result.

IMPORTANT:
- Use ONLY the supplied paper evidence.
- Do not use outside knowledge.
- Do not fabricate contributions or results.
- Maximum 3 primary contributions.
- Maximum 3 secondary contributions.
- Maximum 6 performance items.
- Keep each contribution concise and understandable.
- Return STRICT JSON ONLY.
- No markdown.
- No explanation outside JSON.
If the paper does not provide explicit numerical performance values,
you may describe qualitative experimental findings.

Do not return empty contribution lists when the supplied paper
clearly describes a proposed architecture, method, or experiment.

Use the abstract, introduction, method and results together.

JSON FORMAT:

{{
    "primary_contributions": [
        "Contribution 1",
        "Contribution 2"
    ],
    "secondary_contributions": [
        "Contribution 1",
        "Contribution 2"
    ],
    "performance_summary": [
        {{
            "metric": "Metric or result name",
            "value": "Reported value"
        }}
    ]
}}

PAPER EVIDENCE:

{text}
"""

        return self.llm(prompt)