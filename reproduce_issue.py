
from typing import List, Dict, Any

from itertools import islice

def select_sections(chunks: List[Dict[str, Any]], allowed_sections: List[str], max_chunks: int = 6) -> List[Dict[str, Any]]:
    filtered_chunks = [
        c for c in chunks
        if c.get("section") in allowed_sections
    ]
    # Replicating the problematic line exactly
    return list(islice(filtered_chunks, max_chunks))

def test():
    data = [{"section": "intro", "text": "foo"}, {"section": "other", "text": "bar"}]
    result = select_sections(data, ["intro"], max_chunks=1)
    print(f"Result: {result}")
    assert len(result) == 1

if __name__ == "__main__":
    test()
