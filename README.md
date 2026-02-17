# PaperInsight

PaperInsight is a research paper understanding system that helps you quickly extract the most important insights from academic papers — without reading everything line by line.

It turns complex research papers into a structured decision dashboard that shows:

-  Core problem
-  Methods & models used
-  Best performance results
-  Limitations & risks
-  When to use / not use the research

---

##  Why I Built This

Reading research papers is time-consuming and mentally heavy — especially when you're just trying to understand:

- What did they actually contribute?
- What was the best result?
- Is it reliable?
- Should I use this paper for my project?

PaperInsight solves that by automatically extracting structured insights using LLM-based reasoning and semantic retrieval.

---

##  Architecture Overview

PaperInsight follows a modular pipeline:

1. **File Loader**
   - Supports PDF, DOCX, TXT, ZIP
2. **Text Normalization**
   - Cleans and prepares raw paper text
3. **Section Chunking**
   - Splits into Abstract, Method, Results, etc.
4. **LLM Agents**
   - Section Understanding Agent
   - Contribution Extraction Agent
   - Limitation Analysis Agent
   - Explanation Agent
5. **Performance Metric Cleaner**
   - Keeps only the best metric per type (Accuracy, AUC, F1)
6. **Vector Store + Retrieval**
   - Enables semantic Q&A on the paper
7. **Interactive Web Dashboard (Flask)**

---

##  Key Features

- Extracts structured research summaries
- Identifies best performance metrics only
- Removes duplicate or intermediate results
- Shows performance chart (Accuracy / AUC / F1)
- Risk & limitation analysis
- Beginner-friendly explanation mode
- Paper Q&A using embeddings

---

##  Tech Stack

- Python
- Flask
- Sentence Transformers
- FAISS (vector search)
- OpenAI / LLM integration
- Chart.js (frontend visualization)

---

##  Project Structure

agents/ → LLM reasoning modules
core/ → chunking, embeddings, vector store
loaders/ → PDF / DOCX / TXT parsers
web/ → Flask app + templates


---

##  How to Run Locally

1. Clone the repository:

```bash
git clone https://github.com/rambaburavi/paperinsight.git
cd paperinsight

2. Create a virtual environment:

python -m venv venv
venv\Scripts\activate  # Windows

3. Install dependencies:

pip install -r requirements.txt


4. Run the app:

python -m web.app

Built by Rambabu R
Engineering Student | ML Enthusiast
Then open:

http://127.0.0.1:5000
