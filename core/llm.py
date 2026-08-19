from groq import Groq
import os

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

MODEL = "openai/gpt-oss-20b"


def call_llm(prompt):

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise research paper "
                    "analysis assistant. "
                    "Use only the supplied paper content. "
                    "Do not invent facts. "
                    "Always complete the requested JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=2048
    )

    return response.choices[0].message.content.strip()