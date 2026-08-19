# PaperInsight

Most research papers take 30–60 minutes to properly read. A large part of that time is spent figuring out what the authors actually did, what they contributed, how well it performed, what limitations exist, and whether the research is relevant to a particular use case.

**PaperInsight** automates that first-pass analysis.

Upload a research paper and get a structured research dashboard containing the paper's core problem, proposed approach, contributions, reported performance, limitations, assumptions, and practical usage guidance.

**→ [Live Demo](https://paperinsight-8peu.onrender.com)**

---

## What PaperInsight extracts

Every paper analyzed by PaperInsight produces a structured breakdown:

- **Abstract** — concise explanation of the paper and its main finding
- **Introduction & Research Gap** — what problem exists and why the paper was proposed
- **Primary Contributions** — the main technical contributions
- **Secondary Contributions** — supporting or additional contributions
- **Performance Results** — reported metrics and values extracted from the paper
- **Data Limitations** — limitations related to datasets and training/evaluation data
- **Methodological Risks** — weaknesses or risks in the proposed methodology
- **Generalization Risks** — situations where the approach may not generalize
- **Key Assumptions** — assumptions the proposed method depends on
- **Reliability Assessment** — an evidence-based assessment of the paper
- **Confidence Level** — confidence in the generated assessment
- **When to Use** — situations where the research may be useful
- **When NOT to Use** — situations where the approach may not be suitable
- **Future Scope** — potential research directions derived from the analysis

The result is presented as a structured dashboard rather than a long block of generated text.

---

## How it works

PaperInsight uses a compact two-stage LLM analysis architecture designed to reduce unnecessary LLM calls while keeping the output structured.

```text
Input
(PDF / DOCX / TXT / ZIP)
        ↓
File Detection & Loading
        ↓
Text Normalization
        ↓
Structured Section Chunking
        ↓
Section Selection
 ┌──────────────┬──────────────┬──────────────┬──────────────┐
 │   Overview   │    Method    │   Results    │ Limitations  │
 └──────────────┴──────────────┴──────────────┴──────────────┘
        ↓
Compact Evidence Builder
        ↓
LLM Call #1
Paper Analysis Agent
        │
        ├── Abstract
        ├── Introduction
        ├── Primary Contributions
        ├── Secondary Contributions
        ├── Performance Results
        ├── Data Limitations
        ├── Methodological Risks
        ├── Generalization Risks
        └── Key Assumptions
        ↓
Structured JSON Validation
        ↓
LLM Call #2
Decision / Explanation Agent
        │
        ├── Reliability
        ├── Confidence Level
        ├── When to Use
        ├── When NOT to Use
        └── Future Scope
        ↓
Performance Metric Cleaning
        ↓
Flask Dashboard

## Run it locally

```bash
git clone https://github.com/rambaburavi/paperinsight.git
cd paperinsight

python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

python -m web.app
```

Open `http://127.0.0.1:5000` and upload any research paper PDF.

---

## Project layout

```
agents/   → the 4 LLM reasoning modules
core/     → section chunking, embeddings, FAISS vector store
loaders/  → PDF / DOCX / TXT / ZIP parsers
web/      → Flask app and Jinja2 templates
```

---

Built by [Rambabu R](https://github.com/rambaburavi) — B.E. CSE (AI/ML), KPRIET
