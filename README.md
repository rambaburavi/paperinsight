# PaperInsight

Most research papers take 30–60 minutes to properly read. Half that time is spent figuring out what the authors actually did, what their best result was, and whether any of it is usable. PaperInsight handles that part automatically.

Upload a paper. Get back a structured breakdown: the core problem, what methods they used, their best performance numbers, limitations, and whether the research is actually applicable to your use case.

**→ [Live Demo](https://paperinsight-8peu.onrender.com)**

---

## What gets extracted

Every paper run through PaperInsight produces:

- **Core problem** — what gap the paper is addressing
- **Methods & models** — what approach they took
- **Best performance results** — cleaned and deduplicated (more on this below)
- **Limitations & risks** — what the authors admit won't work
- **Use / don't use guidance** — concrete signal on applicability

The output renders as a structured dashboard, not a wall of text.

---

## How it works

The pipeline has 7 stages:

```
Input (PDF / DOCX / TXT / ZIP)
    ↓
Text Normalization       — strips noise, normalizes whitespace and formatting
    ↓
Section Chunking         — splits into Abstract, Method, Results, Conclusion
    ↓
LLM Agents (4 agents run in sequence)
    ├── Section Understanding Agent   — maps what each section is doing
    ├── Contribution Extraction Agent — pulls out what's actually novel
    ├── Limitation Analysis Agent     — finds caveats, failure modes, scope
    └── Explanation Agent             — rewrites findings in plain language
    ↓
Performance Metric Cleaner
    — papers report the same metric (e.g. Accuracy) across abstract,
      results table, and conclusion. This keeps only the best value
      per metric type (Accuracy / AUC / F1) and drops the rest
    ↓
Flask Dashboard          — renders everything as a structured visual output
```

---

## The metric deduplication problem

Research papers have a habit of mentioning the same number in three different places. You'll see "94.2% accuracy" in the abstract, again in the results table, and again in the conclusion. If you just extract everything, you surface the same fact three times and it looks messy.

The Performance Metric Cleaner solves this by canonicalizing per metric type — it identifies all instances of each metric, keeps the highest reported value, and discards intermediate or repeated entries. The result is a clean performance chart that shows one number per metric, not a cluttered list.

---

## Tech stack

| What | How |
|---|---|
| Backend | Flask (Python) |
| File parsing | PyPDF2, python-docx, zipfile |
| Text chunking | Custom section splitter |
| LLM reasoning | 4 specialized agents via OpenAI-compatible API |
| Semantic search | Sentence Transformers + FAISS |
| Frontend charts | Chart.js |
| Deployment | Render |

---

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
