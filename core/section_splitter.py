import re

SECTION_PATTERNS = {
    "abstract": r"^\s*abstract\s*$",
    "introduction": r"^\s*(\d+\.\s*)?introduction\s*$",
    "method": r"^\s*(\d+\.\s*)?(materials and methods|methodology|methods)\s*$",
    "results": r"^\s*(\d+\.\s*)?results?\s*$",
    "discussion": r"^\s*(\d+\.\s*)?discussion\s*$",
    "limitations": r"^\s*(\d+\.\s*)?limitations?\s*$",
    "conclusion": r"^\s*(\d+\.\s*)?conclusions?\s*$",
}

def split_into_sections(text: str):
    sections = {}
    current_section = "unknown"
    buffer = []

    for line in text.split("\n"):
        stripped = line.strip().lower()
        matched = False

        for section, pattern in SECTION_PATTERNS.items():
            if re.match(pattern, stripped):
                sections.setdefault(current_section, "")
                sections[current_section] += "\n".join(buffer)

                current_section = section
                buffer = []
                matched = True
                break

        if not matched:
            buffer.append(line)

    sections.setdefault(current_section, "")
    sections[current_section] += "\n".join(buffer)

    return sections
