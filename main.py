# ===============================
# STEP 0: Imports
# ===============================

from loaders.file_detector import detect_file_type
from loaders.pdf_loader import load_pdf
from loaders.docx_loader import load_docx
from loaders.text_loader import load_text
from loaders.zip_loader import load_zip

from core.normalize_text import normalize
from core.build_chunks import build_structured_chunks
from core.llm import call_llm

from core.embedder import Embedder
from core.vector_store import VectorStore
from core.retriever import (
    retrieve_semantic_chunks,
    retrieve_keyword_chunks
)

from agents.section_agent import SectionUnderstandingAgent
from agents.contribution_agent import ContributionExtractionAgent
from agents.limitation_agent import LimitationAssumptionAgent
from agents.explanation_agent import ExplanationAgent
from agents.qa_agent import PaperQAAgent


# ===============================
# STEP 0: File Loader
# ===============================

def load_input_file(file_path):
    ext = detect_file_type(file_path)

    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext == ".docx":
        return load_docx(file_path)
    elif ext in [".txt", ".md"]:
        return load_text(file_path)
    elif ext == ".zip":
        return load_zip(file_path)
    else:
        raise ValueError("Unsupported file type")


# ===============================
# MAIN PIPELINE
# ===============================

def main():
    FILE_PATH = "data/inputs/sample.pdf"

    # ---- Step 0: Load & Normalize ----
    raw_text = load_input_file(FILE_PATH)
    clean_text = normalize(raw_text)

    # ---- Step 1: Chunking ----
    chunks = build_structured_chunks(clean_text)

    # ---- Step 2: Section Understanding ----
    abstract_chunks = [c for c in chunks if c["section"] == "abstract"]
    section_agent = SectionUnderstandingAgent(call_llm, "Abstract")
    section_summary = section_agent.run(abstract_chunks)

    print("\n===== ABSTRACT =====\n", section_summary)

    # ---- Step 3: Contributions ----
    contribution_sections = [
        "introduction", "method", "methodology", "approach", "results"
    ]
    contribution_chunks = [
        c for c in chunks if c["section"] in contribution_sections
    ]

    contribution_agent = ContributionExtractionAgent(call_llm)
    contributions = contribution_agent.run(contribution_chunks)

    print("\n===== CONTRIBUTIONS =====\n", contributions)

    # ---- Step 4: Limitations ----
    limitation_sections = [
        "method", "methodology", "approach",
        "experiment", "results",
        "discussion", "conclusion", "limitations"
    ]
    limitation_chunks = [
        c for c in chunks if c["section"] in limitation_sections
    ]

    limitation_agent = LimitationAssumptionAgent(call_llm)
    limitations = limitation_agent.run(limitation_chunks)

    print("\n===== LIMITATIONS =====\n", limitations)

    # ---- Step 5: User-Level Explanation ----
    explanation_agent = ExplanationAgent(call_llm, level="beginner")
    final_explanation = explanation_agent.run(
        section_summary,
        contributions,
        limitations
    )

    print("\n===== FINAL EXPLANATION =====\n", final_explanation)

    # ---- Step 7: Build Embedding Index (BEFORE Q&A) ----
    embedder = Embedder()
    chunk_texts = [c["text"] for c in chunks]
    chunk_embeddings = embedder.embed(chunk_texts)

    vector_store = VectorStore(dim=chunk_embeddings.shape[1])
    vector_store.add(chunk_embeddings, chunks)

    # ---- Step 6: Paper Grounded Q&A ----
    qa_agent = PaperQAAgent(call_llm)

    while True:
        question = input("\nAsk a question about the paper (or type 'exit'): ")
        if question.lower() == "exit":
            break

        # Semantic retrieval (default)
        relevant_chunks = retrieve_semantic_chunks(
            question,
            embedder,
            vector_store,
            top_k=5
        )

        # Keyword fallback
        if not relevant_chunks:
            relevant_chunks = retrieve_keyword_chunks(
                chunks,
                question
            )

        if not relevant_chunks:
            print("No relevant information found in the paper.")
            continue

        answer = qa_agent.run(question, relevant_chunks)
        print("\n===== ANSWER =====\n", answer)


# ===============================
# ENTRY POINT
# ===============================

if __name__ == "__main__":
    main()
