import re

def normalize_to_bullets(text, max_items=6):
    if not text:
        return []

    # Remove markdown bold/italics
    text = re.sub(r"\*\*", "", text)
    text = re.sub(r"\*", "", text)

    # Replace weird bullets
    text = text.replace("•", "\n- ")

    lines = text.split("\n")

    bullets = []
    for line in lines:
        line = line.strip()

        # Accept bullet-like or key-value lines
        if line.startswith("-") or ":" in line:
            clean = re.sub(r"^[-\s]+", "", line)
            clean = clean.strip()
            if len(clean) > 15:
                bullets.append(clean)

        if len(bullets) >= max_items:
            break

    return bullets
