from flask import Flask, render_template, request, redirect, url_for
import os
import json

from loaders.file_detector import detect_file_type
from loaders.pdf_loader import load_pdf
from loaders.docx_loader import load_docx
from loaders.text_loader import load_text
from loaders.zip_loader import load_zip

from core.normalize_text import normalize
from core.build_chunks import build_structured_chunks
from core.llm import call_llm

# from core.embedder import Embedder
# from core.vector_store import VectorStore
# from core.retriever import retrieve_semantic_chunks

from agents.section_agent import SectionUnderstandingAgent
from agents.contribution_agent import ContributionExtractionAgent
from agents.limitation_agent import LimitationAssumptionAgent
from agents.explanation_agent import ExplanationAgent
from agents.qa_agent import PaperQAAgent


# ================== APP SETUP ==================
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

stored_result = {}
stored_level = "beginner"
stored_chunks = []
stored_embedder = None
stored_vector_store = None


# ================== SAFE JSON PARSER ==================
import json
import re

def safe_json_parse(raw, fallback):
    if not raw:
        return fallback

    try:
        # Extract JSON between first { and last }
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            cleaned = match.group(0)
            return json.loads(cleaned)
        else:
            return fallback
    except Exception:
        return fallback



# ================== FALLBACK STRUCTURES ==================
ABSTRACT_FALLBACK = {
    "problem": "Not explicitly stated",
    "dataset": "Not explicitly stated",
    "method": "Not explicitly stated",
    "model": "Not explicitly stated",
    "evaluation_metrics": "Not explicitly stated",
    "best_result": "Not explicitly stated",
    "application_domain": "Not explicitly stated"
}

CONTRIBUTION_FALLBACK = {
    "primary_contributions": [],
    "secondary_contributions": [],
    "performance_summary": []
}

LIMITATION_FALLBACK = {
    "data_limitations": [],
    "methodological_risks": [],
    "generalization_risks": [],
    "key_assumptions": []
}

EXPLANATION_FALLBACK = {
    "reliability": "Insufficient information for a confident judgment",
    "confidence_level": "Low",
    "when_to_use": [],
    "when_not_to_use": [],
    "future_scope": ""
}


# ================== FILE LOADER ==================
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

# ================== SECTION SELECTOR ==================
def select_sections(chunks, allowed_sections, max_chunks=5):
    selected = [
        c for c in chunks
        if c.get("section") in allowed_sections
        and c.get("text")
        and len(c["text"].strip()) > 50
    ]
    return selected[:max_chunks]

# ================== PERFORMANCE CLEANER ==================
def keep_best_metrics(metrics):
    best = {}

    for item in metrics:

        metric_name = None
        raw_value = None

        # Format 1: {"metric":"Accuracy", "value":"98.4%"}
        if isinstance(item, dict) and item.get("metric") and item.get("value"):
            metric_name = item["metric"]
            raw_value = item["value"]

        # Format 2: {"accuracy":"98.4%"}
        elif isinstance(item, dict) and "accuracy" in item:
            metric_name = "Accuracy"
            raw_value = item["accuracy"]

        # Format 3: plain string "Accuracy: 98.4%"
        elif isinstance(item, str) and ":" in item:
            parts = item.split(":")
            metric_name = parts[0].strip()
            raw_value = parts[1].strip()

        if metric_name and raw_value:

            cleaned = ''.join(c for c in str(raw_value) if c.isdigit() or c == '.')
            if cleaned:
                value = float(cleaned)

                compare_value = value * 100 if value <= 1 else value

                key = metric_name.lower()

                if key not in best or compare_value > best[key]["numeric"]:
                    best[key] = {
                        "metric": metric_name,
                        "value": raw_value,
                        "numeric": compare_value
                    }

    return [
        {"metric": v["metric"], "value": v["value"]}
        for v in best.values()
    ]



# ================== ROUTES ==================
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    global stored_result, stored_level
    global stored_chunks, stored_embedder, stored_vector_store

    file = request.files["paper"]
    stored_level = request.form.get("level", "beginner")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # -------- Pipeline --------
    raw_text = load_input_file(file_path)
    clean_text = normalize(raw_text)
    chunks = build_structured_chunks(clean_text)
    
    # -------- DEBUG (keep this) --------
    # print("Detected sections:", sorted(set(c["section"] for c in chunks)))
    # print("Total chunks:", len(chunks))

    # -------- FIX-1: POSITION-BASED CHUNKING --------
    # total = len(chunks)

    # overview_chunks = [c for c in chunks if c["section"] == "abstract"][:6]

    # method_chunks = [c for c in chunks if c["section"] == "method"][:6]

    # result_chunks = [c for c in chunks if c["section"] == "results"][:6]

    # limitation_chunks = [c for c in chunks if c["section"] in ["discussion", "limitations", "conclusion"]][:6]
    total = len(chunks)

    # 1️⃣ Overview
    overview_chunks = select_sections(
        chunks, ["abstract", "introduction"], max_chunks=5
    )

    if not overview_chunks:
        overview_chunks = chunks[:5]

    # 2️⃣ Method
    method_chunks = select_sections(
        chunks, ["method", "methodology", "approach"], max_chunks=5
    )

    if not method_chunks:
        method_chunks = chunks[int(total * 0.2): int(total * 0.4)]

    # 3️⃣ Results
    result_chunks = select_sections(
        chunks, ["results", "experiment"], max_chunks=5
    )

    if not result_chunks:
        result_chunks = chunks[int(total * 0.4): int(total * 0.6)]

    # 4️⃣ Limitations
    limitation_chunks = select_sections(
        chunks, ["limitations", "discussion", "conclusion"], max_chunks=5
    )

    if not limitation_chunks:
        limitation_chunks = chunks[int(total * 0.7):]

    # print("Detected sections:", sorted(set(c["section"] for c in chunks)))
    # print("Overview chunks:", len(overview_chunks))

    # print("Overview chunks:", len(overview_chunks))
    # print("Method chunks:", len(method_chunks))
    # print("Result chunks:", len(result_chunks))
    # print("Limitation chunks:", len(limitation_chunks))

    # # 🔍 DEBUG (keep for now)
    # print("Detected sections:", sorted(set(c["section"] for c in chunks)))
    # print("Sample chunk text:", chunks[0]["text"][:300])

    # print("Total chunks:", len(chunks))

    # # ===== TEMPORARY POSITION-BASED SELECTION (ROBUST) =====
    # overview_chunks = chunks[:4]
    # method_chunks = chunks[4:10]
    # result_chunks = chunks[10:16]
    # limitation_chunks = chunks[-6:]

    # print("Overview chunks:", len(overview_chunks))
    # print("Method chunks:", len(method_chunks))
    # print("Result chunks:", len(result_chunks))
    # print("Limitation chunks:", len(limitation_chunks))

    # -------- Agents --------
    section_agent = SectionUnderstandingAgent(call_llm)
    contribution_agent = ContributionExtractionAgent(call_llm)
    limitation_agent = LimitationAssumptionAgent(call_llm)
    explanation_agent = ExplanationAgent(call_llm, stored_level)

    overview_raw = section_agent.run(overview_chunks)
    # 🔒 HARD LIMIT: max 5 chunks total
    contribution_chunks = (overview_chunks+method_chunks + result_chunks)
    contribution_raw = contribution_agent.run(contribution_chunks)
    #print("RAW CONTRIBUTION OUTPUT:", contribution_raw)
    limitation_raw = limitation_agent.run(limitation_chunks)
    explanation_raw = explanation_agent.run(
        overview_raw, contribution_raw, limitation_raw
    )

    # -------- Safe Parsing --------
    abstract_data = safe_json_parse(overview_raw, ABSTRACT_FALLBACK)
    contribution_data = safe_json_parse(contribution_raw, CONTRIBUTION_FALLBACK)
    limitation_data = safe_json_parse(limitation_raw, LIMITATION_FALLBACK)
    explanation_data = safe_json_parse(explanation_raw, EXPLANATION_FALLBACK)

    # 🔥 Clean performance metrics (keep highest per metric)
    if "performance_summary" in contribution_data:
        contribution_data["performance_summary"] = keep_best_metrics(
            contribution_data.get("performance_summary", [])
        )
    print("CLEANED PERFORMANCE:", contribution_data.get("performance_summary"))

    stored_result = {
        "abstract": abstract_data,
    "contributions": contribution_data,
    "limitations": limitation_data,
    "explanation": explanation_data
}


    # -------- Embeddings for Q&A --------
    # embedder = Embedder()
    # valid_chunks = [c for c in chunks if c.get("text", "").strip()]
    # texts = [c["text"] for c in valid_chunks]

    # embeddings = embedder.embed(texts)
    # vector_store = VectorStore(dim=embeddings.shape[1])
    # vector_store.add(embeddings, valid_chunks)

    # stored_chunks = valid_chunks
    # stored_embedder = embedder
    # stored_vector_store = vector_store

    return redirect(url_for("results"))


@app.route("/results", methods=["GET"])
def results():
    if not stored_result:
        return redirect(url_for("index"))

    return render_template(
        "results.html",
        result=stored_result,
        level=stored_level
    )


# @app.route("/ask", methods=["POST"])
# def ask():
#     question = request.form["question"]

#     qa_agent = PaperQAAgent(call_llm)
#     relevant_chunks = retrieve_semantic_chunks(
#         question, stored_embedder, stored_vector_store
#     )

#     answer = qa_agent.run(question, relevant_chunks)
#     return answer


@app.route("/feedback")
def feedback():
    return render_template("feedback.html")


if __name__ == "__main__":
    app.run()
