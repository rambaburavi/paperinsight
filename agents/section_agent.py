class SectionUnderstandingAgent:
    def __init__(self, llm, section_name="Abstract & Introduction"):
        self.llm = llm
        self.section_name = section_name

    def run(self, chunks):
        if not chunks:
            return {
                "abstract": "No abstract evidence was found in the uploaded paper.",
                "introduction": "No introduction evidence was found in the uploaded paper."
            }

        text_parts = []

        for chunk in chunks:
            text = chunk.get("text", "").strip()

            if text:
                text_parts.append(text)

        if not text_parts:
            return {
                "abstract": "No abstract evidence was found in the uploaded paper.",
                "introduction": "No introduction evidence was found in the uploaded paper."
            }

        paper_text = "\n\n".join(text_parts)

        # Keep enough context for both sections
        paper_text = paper_text[:12000]

        prompt = f"""
You are a research-paper analysis assistant.

Analyze the following extracted text from a research paper.

Your task is to produce TWO concise sections:

ABSTRACT
Summarize the paper's abstract. Explain:
- the main research problem
- the proposed approach
- the main objective or finding

INTRODUCTION

Explain the research motivation and problem in 3-5 clear sentences.

The explanation must cover:
- Why the problem matters
- What is wrong with existing approaches
- What research gap the authors identify
- What the proposed work does differently

Do NOT describe implementation details.
Do NOT repeat the abstract word-for-word.
Do NOT include citations.
Do NOT include section numbers.
Do NOT include raw paper text.
Keep it understandable to a beginner.
- The Introduction must be a maximum of 120 words.
- Never output "PAPER TEXT:".
- Never reproduce the supplied paper text.
- Only output the requested summaries.

IMPORTANT:
- Use ONLY the supplied paper text.
- Do NOT use outside knowledge.
- Do NOT invent information.
- Do NOT discuss datasets, metrics, or results unless they are actually
  present in the supplied text.
- Write for a beginner who understands basic AI/ML concepts.
- Each section should be one clear paragraph.
- Do not write bullet points.
- Do not write markdown.
- Do not add any explanation before or after the answer.

Return exactly this format:

ABSTRACT:
<abstract summary>

INTRODUCTION:
<introduction summary>

PAPER TEXT:
{paper_text}
"""

        raw = self.llm(prompt)

        if not raw:
            return {
                "abstract": "The abstract could not be extracted from the available paper text.",
                "introduction": "The introduction could not be extracted from the available paper text."
            }

        # Parse the model's simple text format instead of depending
        # completely on JSON formatting.
        abstract = ""
        introduction = ""

        upper = raw.upper()

        abstract_marker = "ABSTRACT:"
        introduction_marker = "INTRODUCTION:"

        abstract_start = upper.find(abstract_marker)
        introduction_start = upper.find(introduction_marker)

        if abstract_start != -1:
            abstract_start += len(abstract_marker)

            if introduction_start != -1:
                abstract = raw[abstract_start:introduction_start].strip()
            else:
                abstract = raw[abstract_start:].strip()

        if introduction_start != -1:
            introduction_start += len(introduction_marker)

            introduction = raw[introduction_start:].strip()

            # Remove anything accidentally echoed after the answer
            paper_text_marker = introduction.upper().find("PAPER TEXT:")

            if paper_text_marker != -1:
                introduction = introduction[:paper_text_marker].strip()

        if not abstract:
            abstract = "The abstract could not be extracted from the available paper text."

        if not introduction:
            introduction = "The introduction could not be extracted from the available paper text."

        return {
            "abstract": abstract,
            "introduction": introduction
        }