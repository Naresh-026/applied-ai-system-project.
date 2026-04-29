import json
from pathlib import Path

_PATTERNS_PATH = Path(__file__).parent.parent / "data" / "bug_patterns.json"


def _load_patterns() -> list[dict]:
    with open(_PATTERNS_PATH) as f:
        return json.load(f)


def retrieve_relevant_patterns(code: str, top_k: int = 3) -> list[dict]:
    """Keyword-based retrieval: score each pattern against the code, return top_k."""
    patterns = _load_patterns()
    code_lower = code.lower()

    scored = []
    for p in patterns:
        score = sum(1 for kw in p["keywords"] if kw.lower() in code_lower)
        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_k]]


def format_context(patterns: list[dict]) -> str:
    """Render retrieved patterns as a readable context block for the LLM."""
    if not patterns:
        return "No specific bug patterns retrieved from knowledge base."

    lines = ["## Retrieved Bug Patterns (Knowledge Base)\n"]
    for i, p in enumerate(patterns, 1):
        lines += [
            f"### Pattern {i} [{p['id']}]: {p['category']} — {p['pattern']}",
            f"- **Description:** {p['description']}",
            f"- **Buggy example:** `{p['example_bug']}`",
            f"- **Fixed example:** `{p['example_fix']}`",
            f"- **Why it matters:** {p['explanation']}\n",
        ]
    return "\n".join(lines)
