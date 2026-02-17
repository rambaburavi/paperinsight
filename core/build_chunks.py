from core.section_splitter import split_into_sections
from core.chunker import chunk_text


def infer_section_from_text(text: str) -> str:
    """
    Fallback section inference when section_splitter fails.
    Looks only at the beginning of the text (cheap + safe).
    """
    t = text.lower()[:300]

    if "abstract" in t:
        return "abstract"
    if "introduction" in t:
        return "introduction"
    if "method" in t or "methodology" in t or "approach" in t:
        return "method"
    if "result" in t or "experiment" in t:
        return "results"
    if "discussion" in t:
        return "discussion"
    if "conclusion" in t:
        return "conclusion"
    if "limitation" in t:
        return "limitations"

    return "unknown"


def build_structured_chunks(text):
    sections = split_into_sections(text)
    structured_chunks = []

    for section, content in sections.items():
        chunks = chunk_text(content)

        for idx, chunk in enumerate(chunks):
            inferred_section = section

            # 🔥 CRITICAL FIX: infer section if unknown
            if section == "unknown":
                inferred_section = infer_section_from_text(chunk)

            structured_chunks.append({
                "section": inferred_section,
                "chunk_id": idx,
                "text": chunk.strip()
            })

    # 🔥 FINAL SAFETY NET: FORCE ABSTRACT IF STILL MISSING
    has_abstract = any(
        c["section"] in ["abstract", "introduction"]
        for c in structured_chunks
    )

    if not has_abstract:
        for i in range(min(4, len(structured_chunks))):
            structured_chunks[i]["section"] = "abstract"

    return structured_chunks
