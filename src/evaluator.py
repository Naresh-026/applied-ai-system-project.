"""Evaluation harness — tests the AI agent on known-buggy and clean code snippets."""
from src.ai_agent import analyze_code

EVAL_CASES = [
    {
        "name": "Inverted comparison hints",
        "code": (
            "def check_guess(guess, secret):\n"
            "    if guess == secret:\n"
            "        return 'Win'\n"
            "    if guess > secret:\n"
            "        return 'Too Low'   # BUG: should be Too High\n"
            "    return 'Too High'      # BUG: should be Too Low\n"
        ),
        "expected_keywords": ["invert", "swap", "wrong", "too high", "too low", "hint"],
        "should_find_bug": True,
    },
    {
        "name": "Secret regenerated on every Streamlit rerun",
        "code": (
            "import random\n"
            "import streamlit as st\n\n"
            "secret = random.randint(1, 100)  # BUG: not in session_state\n\n"
            "if st.button('Submit'):\n"
            "    if int(st.text_input('Guess')) == secret:\n"
            "        st.success('You won!')\n"
        ),
        "expected_keywords": ["session_state", "regenerat", "rerun", "persist"],
        "should_find_bug": True,
    },
    {
        "name": "Wrong difficulty ranges (Easy too hard)",
        "code": (
            "def get_range_for_difficulty(difficulty):\n"
            "    if difficulty == 'Easy':\n"
            "        return 1, 100   # BUG: Easy should be 1-20\n"
            "    if difficulty == 'Normal':\n"
            "        return 1, 20    # BUG: Normal should be 1-50\n"
            "    return 1, 50        # BUG: Hard should be 1-100\n"
        ),
        "expected_keywords": ["easy", "hard", "range", "difficul", "swap"],
        "should_find_bug": True,
    },
    {
        "name": "Clean correct code (no bugs)",
        "code": (
            "def check_guess(guess: int, secret: int) -> str:\n"
            "    if guess == secret:\n"
            "        return 'Win'\n"
            "    if guess > secret:\n"
            "        return 'Too High'\n"
            "    return 'Too Low'\n"
        ),
        "expected_keywords": [],
        "should_find_bug": False,
    },
]


def run_evaluation() -> dict:
    """Run all eval cases. Returns summary dict."""
    results = []
    for case in EVAL_CASES:
        print(f"  Testing: {case['name']} ...", flush=True)
        result = analyze_code(case["code"])

        if result.get("error"):
            results.append({
                "name": case["name"],
                "passed": False,
                "reason": f"Error: {result['error']}",
                "confidence": 0,
            })
            continue

        raw_lower = result["raw"].lower()

        if case["should_find_bug"]:
            keyword_hit = any(kw in raw_lower for kw in case["expected_keywords"])
            passed = keyword_hit and result["confidence"] >= 50
            reason = "Bug detected correctly" if passed else "Missed bug or low confidence"
        else:
            no_bug_signals = (
                "no bug" in raw_lower
                or "no issues" in raw_lower
                or "clean" in raw_lower
                or len(result["bugs"]) == 0
            )
            passed = no_bug_signals and result["confidence"] >= 70
            reason = "Correctly identified clean code" if passed else "False positive or low confidence"

        results.append({
            "name": case["name"],
            "passed": passed,
            "reason": reason,
            "confidence": result["confidence"],
        })

    passed_count = sum(1 for r in results if r["passed"])
    avg_conf = sum(r["confidence"] for r in results) / len(results) if results else 0
    return {
        "results": results,
        "passed": passed_count,
        "total": len(results),
        "avg_confidence": round(avg_conf, 1),
    }
