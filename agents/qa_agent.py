class PaperQAAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, question, chunks):
        context = "\n\n".join(c["text"] for c in chunks)

        prompt = """
Answer the question ONLY using the paper content below.
If the answer is not present, say: "The paper does not provide this information."

Question:
{question}

Paper content:
{context}
"""
        return self.llm(prompt)
