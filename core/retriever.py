# ===============================
# STEP 6: Baseline Keyword Retriever
# ===============================
def retrieve_keyword_chunks(chunks, question, max_chunks=5):
    question_words = set(question.lower().split())
    scored = []

    for c in chunks:
        text_words = set(c["text"].lower().split())
        score = len(question_words & text_words)

        if score > 0:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:max_chunks]]


# ===============================
# STEP 7: Semantic Retriever
# ===============================
def retrieve_semantic_chunks(question, embedder, vector_store, top_k=5):
    q_embedding = embedder.embed([question])
    return vector_store.search(q_embedding, top_k=top_k)
