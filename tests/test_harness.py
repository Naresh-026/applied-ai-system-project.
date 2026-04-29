"""
Automated reliability evaluation for the AI Code Bug Analyst.

Usage:
    python3 -m tests.test_harness
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluator import run_evaluation

SEP = "=" * 62


def main() -> None:
    print(f"\n{SEP}")
    print("  AI CODE BUG ANALYST — RELIABILITY EVALUATION HARNESS")
    print(SEP)

    summary = run_evaluation()

    print(f"\n{SEP}")
    print("  RESULTS")
    print(SEP)
    for r in summary["results"]:
        icon = "✅" if r["passed"] else "❌"
        print(f"{icon} {r['name']}")
        print(f"   Confidence: {r['confidence']}% | {r['reason']}")

    print(f"\n{'-' * 62}")
    print(f"  Score         : {summary['passed']}/{summary['total']} passed")
    print(f"  Avg Confidence: {summary['avg_confidence']}%")

    if summary["passed"] == summary["total"]:
        print("  Result        : ✅ All tests passed!")
    else:
        failed = summary["total"] - summary["passed"]
        print(f"  Result        : ⚠️  {failed} test(s) failed — review logs/ai_agent.log")

    print(SEP + "\n")


if __name__ == "__main__":
    main()
