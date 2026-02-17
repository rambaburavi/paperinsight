import zipfile
import os
from loaders.pdf_loader import load_pdf
from loaders.docx_loader import load_docx
from loaders.text_loader import load_text

def load_zip(path, extract_to="data/temp"):
    os.makedirs(extract_to, exist_ok=True)
    text = ""

    with zipfile.ZipFile(path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

    for root, _, files in os.walk(extract_to):
        for file in files:
            full_path = os.path.join(root, file)

            if file.endswith(".pdf"):
                text += load_pdf(full_path)
            elif file.endswith(".docx") or file.endswith(".txt"):
                text += load_text(full_path)

    return text
