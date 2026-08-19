from flask import Flask, render_template, request, redirect, url_for
import os
import json
import re

from loaders.file_detector import detect_file_type
from loaders.pdf_loader import load_pdf
from loaders.docx_loader import load_docx
from loaders.text_loader import load_text
from loaders.zip_loader import load_zip

from core.normalize_text import normalize
from core.build_chunks import build_structured_chunks
from core.llm import call_llm


# ============================================================
# APP SETUP
# ============================================================

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

stored_result = {}
stored_level = "beginner"


# ============================================================
# SAFE JSON PARSER
# ============================================================

def safe_json_parse(raw, fallback):
    
    if not raw:
        return fallback

    raw = raw.strip()

    raw = re.sub(
        r"```json\s*",
        "",
        raw,
        flags=re.IGNORECASE
    )

    raw = re.sub(
        r"```\s*$",
        "",
        raw
    ).strip()

    start = raw.find("{")
    end = raw.rfind("}")

    if start == -1 or end == -1 or end <= start:
        print("JSON object not found.")
        print("RAW OUTPUT:", raw)
        return fallback

    try:
        return json.loads(
            raw[start:end + 1]
        )

    except json.JSONDecodeError as e:

        print("JSON parsing failed:", e)
        print("RAW OUTPUT:", raw)

        return fallback

# ============================================================
# FALLBACK STRUCTURES
# ============================================================

ANALYSIS_FALLBACK = {
    "abstract": (
        "The abstract could not be extracted "
        "from the available paper text."
    ),
    "introduction": (
        "The introduction could not be extracted "
        "from the available paper text."
    ),
    "primary_contributions": [],
    "secondary_contributions": [],
    "performance_summary": [],
    "data_limitations": [],
    "methodological_risks": [],
    "generalization_risks": [],
    "key_assumptions": []
}


EXPLANATION_FALLBACK = {
    "reliability": (
        "Insufficient information for a confident judgment."
    ),
    "confidence_level": "Low",
    "when_to_use": [],
    "when_not_to_use": [],
    "future_scope": ""
}


# ============================================================
# FILE LOADER
# ============================================================

def load_input_file(file_path):

    ext = detect_file_type(file_path)

    if ext == ".pdf":
        return load_pdf(file_path)

    if ext == ".docx":
        return load_docx(file_path)

    if ext in [".txt", ".md"]:
        return load_text(file_path)

    if ext == ".zip":
        return load_zip(file_path)

    raise ValueError("Unsupported file type")


# ============================================================
# SECTION SELECTOR
# ============================================================

def select_sections(
    chunks,
    allowed_sections,
    max_chunks=5
):

    allowed = {
        section.lower().strip()
        for section in allowed_sections
    }

    selected = []

    for chunk in chunks:

        section = str(
            chunk.get("section", "")
        ).lower().strip()

        text = str(
            chunk.get("text", "")
        ).strip()

        if (
            section in allowed
            and text
            and len(text) > 50
        ):
            selected.append(chunk)

    return selected[:max_chunks]


# ============================================================
# COMPACT TEXT BUILDER
# ============================================================

def build_evidence(chunks, max_chars):

    pieces = []
    current_length = 0

    for chunk in chunks:

        text = str(
            chunk.get("text", "")
        ).strip()

        if not text:
            continue

        section = str(
            chunk.get("section", "unknown")
        ).strip()

        piece = (
            f"[SECTION: {section}]\n"
            f"{text}"
        )

        if (
            current_length + len(piece)
            > max_chars
        ):
            break

        pieces.append(piece)
        current_length += len(piece)

    return "\n\n".join(pieces)


# ============================================================
# PERFORMANCE CLEANER
# ============================================================

def clean_performance_metrics(metrics):
    
    cleaned = []

    if not isinstance(metrics, list):
        return cleaned

    for item in metrics:

        if isinstance(item, dict):

            metric = item.get("metric")
            value = item.get("value")

            if metric and value:
                cleaned.append({
                    "metric": str(metric).strip(),
                    "value": str(value).strip()
                })

        elif isinstance(item, str):

            if ":" in item:

                metric, value = item.split(":", 1)

                cleaned.append({
                    "metric": metric.strip(),
                    "value": value.strip()
                })

    return cleaned

# ============================================================
# FIRST LLM CALL
# COMPLETE PAPER ANALYSIS
# ============================================================

def analyze_paper_with_llm(evidence):

    prompt = f"""
You are PaperInsight, a research-paper analysis system.

Analyze ONLY the supplied paper evidence.

Your job is to create a compact but accurate structured
understanding of the paper.

IMPORTANT:
- Use only information present in the supplied evidence.
- Do not use outside knowledge.
- Do not invent datasets, models, metrics, results, limitations,
  or claims.
- If information is genuinely unavailable, return an empty
  list or a short "Not explicitly stated" statement.
- Do not confuse the paper's motivation with its contribution.
- Do not repeat the same idea across multiple sections.
- Keep the output concise.
- Return ONLY valid JSON.
- Do not use markdown.
- Do not add explanations outside JSON.

Return EXACTLY this structure:

{{
  "abstract": "One concise paragraph summarizing the paper's
research problem, proposed approach, and main finding.",

  "introduction": "One concise paragraph explaining the
motivation, existing problem, research gap, and proposed idea.",

  "primary_contributions": [
    "Most important contribution.",
    "Second important contribution.",
    "Third important contribution."
  ],

  "secondary_contributions": [
    "Additional contribution.",
    "Additional contribution."
  ],

  "performance_summary": [
    {{
      "metric": "Metric or benchmark name",
      "value": "Reported result"
    }}
  ],

  "data_limitations": [
    "Limitation supported by the paper."
  ],

  "methodological_risks": [
    "Methodological limitation or risk supported by the paper."
  ],

  "generalization_risks": [
    "Generalization limitation supported by the paper."
  ],

  "key_assumptions": [
    "Important assumption made by the approach."
  ]
}}

QUALITY RULES:

ABSTRACT:
- 3 to 5 sentences.
- Explain what problem the paper solves.
- Explain what it proposes.
- Mention the main experimental finding if available.

INTRODUCTION:
- 3 to 5 sentences.
- Explain the problem.
- Explain why existing approaches are insufficient.
- Explain the research gap.
- Explain what the paper proposes.
- Do NOT copy the abstract.

CONTRIBUTIONS:
- Maximum 3 primary contributions.
- Maximum 3 secondary contributions.
- State actual contributions, not generic claims.

PERFORMANCE:
- Include only results explicitly reported in the evidence.
- Preserve metric names and values.
- Do not invent numbers.

LIMITATIONS:
- Only include limitations supported by the paper.
- Do not manufacture limitations merely because something
  "could" be a limitation.

PAPER EVIDENCE:

{evidence}
"""

    return call_llm(prompt)


# ============================================================
# SECOND LLM CALL
# DECISION / EXPLANATION
# ============================================================

def generate_decision(analysis_data):

    compact_json = json.dumps(
        analysis_data,
        ensure_ascii=False
    )

    prompt = f"""
You are the decision-analysis component of PaperInsight.

Use ONLY the structured paper analysis below.

Do not introduce facts that are not present in it.

Create a concise beginner-friendly decision summary.

Return ONLY valid JSON.

Required structure:

{{
  "reliability": "A concise 3-5 sentence assessment of how
reliable the paper's evidence and conclusions appear.",

  "confidence_level": "High / Moderate-High / Moderate /
Low",

  "when_to_use": [
    "Appropriate use case.",
    "Appropriate use case.",
    "Appropriate use case."
  ],

  "when_not_to_use": [
    "Situation where the approach may not be suitable.",
    "Situation where the approach may not be suitable."
  ],

  "future_scope": "A concise paragraph describing future
research directions that logically follow from the paper's
limitations or findings."
}}

RULES:

- Do not say the paper is universally reliable.
- Base reliability on the evidence supplied.
- Do not invent deployment results.
- Do not invent future work that contradicts the paper.
- Keep confidence realistic.
- Maximum 4 items for when_to_use.
- Maximum 4 items for when_not_to_use.
- Keep everything concise.

STRUCTURED PAPER ANALYSIS:

{compact_json}
"""

    return call_llm(prompt)


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# ANALYZE
# ============================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    global stored_result
    global stored_level

    # --------------------------------------------------------
    # FILE
    # --------------------------------------------------------

    file = request.files.get("paper")

    if not file or not file.filename:
        return redirect(
            url_for("index")
        )

    stored_level = request.form.get(
        "level",
        "beginner"
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    file.save(file_path)

    print(
        "\n========================================"
    )

    print(
        "STARTING PAPER ANALYSIS"
    )

    print(
        "========================================"
    )

    try:

        # ====================================================
        # 1. LOAD
        # ====================================================

        raw_text = load_input_file(
            file_path
        )

        # ====================================================
        # 2. NORMALIZE
        # ====================================================

        clean_text = normalize(
            raw_text
        )

        # ====================================================
        # 3. CHUNK
        # ====================================================

        chunks = build_structured_chunks(
            clean_text
        )

        total = len(chunks)

        print(
            "Total chunks:",
            total
        )

        detected_sections = sorted(
            set(
                str(
                    chunk.get(
                        "section",
                        ""
                    )
                ).lower().strip()

                for chunk in chunks
            )
        )

        print(
            "Detected sections:",
            detected_sections
        )

        # ====================================================
        # 4. SELECT ONLY IMPORTANT EVIDENCE
        # ====================================================

        overview_chunks = select_sections(
            chunks,
            [
                "abstract",
                "introduction",
                "intro"
            ],
            max_chunks=4
        )

        method_chunks = select_sections(
            chunks,
            [
                "method",
                "methodology",
                "approach"
            ],
            max_chunks=3
        )

        result_chunks = select_sections(
            chunks,
            [
                "results",
                "result",
                "experiment",
                "experiments",
                "evaluation"
            ],
            max_chunks=5
        )

        limitation_chunks = select_sections(
            chunks,
            [
                "limitations",
                "limitation",
                "discussion",
                "conclusion",
                "future work",
                "future_work"
            ],
            max_chunks=4
        )

        # ----------------------------------------------------
        # If section detection misses something, use position
        # based evidence as a small fallback.
        # ----------------------------------------------------

        if not overview_chunks:
            overview_chunks = chunks[:4]

        if not method_chunks:
            method_chunks = chunks[
                int(total * 0.20):
                int(total * 0.35)
            ][:3]

        if not result_chunks:
            result_chunks = chunks[
                int(total * 0.35):
                int(total * 0.60)
            ][:5]

        if not limitation_chunks:
            limitation_chunks = chunks[
                int(total * 0.65):
            ][:4]

        print(
            "Overview chunks:",
            len(overview_chunks)
        )

        print(
            "Method chunks:",
            len(method_chunks)
        )

        print(
            "Result chunks:",
            len(result_chunks)
        )

        print(
            "Limitation chunks:",
            len(limitation_chunks)
        )

        # ====================================================
        # 5. BUILD COMPACT EVIDENCE
        # ====================================================

        selected_chunks = (
            overview_chunks
            + method_chunks
            + result_chunks
            + limitation_chunks
        )

        # Remove duplicate chunks while preserving order
        unique_chunks = []
        seen_text = set()

        for chunk in selected_chunks:

            text = str(
                chunk.get("text", "")
            ).strip()

            if not text:
                continue

            key = text[:300]

            if key in seen_text:
                continue

            seen_text.add(key)
            unique_chunks.append(chunk)

        evidence = build_evidence(
    unique_chunks,
    max_chars=15000
)

        print(
            "Evidence characters:",
            len(evidence)
        )

        # ====================================================
        # 6. LLM CALL #1
        # ====================================================

        print(
            "\nRunning Paper Analysis Agent..."
        )

        analysis_raw = analyze_paper_with_llm(
            evidence
        )

        print(
            "Paper Analysis Agent completed."
        )

        print(
            "\n========== ANALYSIS RAW =========="
        )

        print(
            analysis_raw
        )

        # ====================================================
        # 7. PARSE ANALYSIS
        # ====================================================

        analysis_data = safe_json_parse(
            analysis_raw,
            ANALYSIS_FALLBACK
        )

        # ====================================================
        # 8. LLM CALL #2
        # ====================================================

        print(
            "\nRunning Decision Agent..."
        )

        explanation_raw = generate_decision(
            analysis_data
        )

        print(
            "Decision Agent completed."
        )

        # ====================================================
        # 9. PARSE DECISION
        # ====================================================

        explanation_data = safe_json_parse(
            explanation_raw,
            EXPLANATION_FALLBACK
        )

        # ====================================================
        # 10. BUILD EXISTING DASHBOARD FORMAT
        # ====================================================

        contribution_data = {
            "primary_contributions": analysis_data.get(
                "primary_contributions",
                []
            ),

            "secondary_contributions": analysis_data.get(
                "secondary_contributions",
                []
            ),

            "performance_summary": clean_performance_metrics(
                analysis_data.get(
                    "performance_summary",
                    []
                )
            )
        }

        limitation_data = {
            "data_limitations": analysis_data.get(
                "data_limitations",
                []
            ),

            "methodological_risks": analysis_data.get(
                "methodological_risks",
                []
            ),

            "generalization_risks": analysis_data.get(
                "generalization_risks",
                []
            ),

            "key_assumptions": analysis_data.get(
                "key_assumptions",
                []
            )
        }

        # ====================================================
        # 11. STORE
        # ====================================================

        stored_result = {
            "abstract": {
                "abstract": analysis_data.get(
                    "abstract",
                    ANALYSIS_FALLBACK["abstract"]
                ),

                "introduction": analysis_data.get(
                    "introduction",
                    ANALYSIS_FALLBACK["introduction"]
                )
            },

            "contributions": contribution_data,

            "limitations": limitation_data,

            "explanation": explanation_data
        }

        print(
            "\nCLEANED PERFORMANCE:"
        )

        print(
            contribution_data[
                "performance_summary"
            ]
        )

        print(
            "\n========================================"
        )

        print(
            "PAPER ANALYSIS COMPLETED"
        )

        print(
            "========================================\n"
        )

        return redirect(
            url_for("results")
        )

    except Exception as e:

        print(
            "\n========================================"
        )

        print(
            "ANALYSIS ERROR"
        )

        print(
            e
        )

        print(
            "========================================\n"
        )

        return render_template(
            "index.html",
            error=(
                "Paper analysis failed. "
                "Please try again."
            )
        )


# ============================================================
# RESULTS
# ============================================================

@app.route(
    "/results",
    methods=["GET"]
)
def results():

    if not stored_result:

        return redirect(
            url_for("index")
        )

    return render_template(
        "results.html",
        result=stored_result,
        level=stored_level
    )


# ============================================================
# FEEDBACK
# ============================================================

@app.route("/feedback")
def feedback():

    return render_template(
        "feedback.html"
    )


# ============================================================
# FILE TOO LARGE
# ============================================================

@app.errorhandler(413)
def file_too_large(error):

    return render_template(
        "index.html",
        error=(
            "PDF too large. "
            "Please upload a file smaller than 10 MB."
        )
    ), 413


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run()