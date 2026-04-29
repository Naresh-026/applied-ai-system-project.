"""
Agentic 3-step code analysis pipeline:
  Step 1 — RAG: retrieve relevant bug patterns from the knowledge base
  Step 2 — Plan: Claude outlines its analysis strategy
  Step 3 — Report: Claude produces a structured bug report with confidence score
"""
import os
import re

import anthropic
from dotenv import load_dotenv

from src.rag_retriever import retrieve_relevant_patterns, format_context
from src.logger import logger, log_analysis, check_guardrails

load_dotenv()

MODEL = "claude-sonnet-4-6"

_SYSTEM = """You are an expert Python code reviewer who specialises in finding subtle bugs.

You follow a strict 3-step agentic process — label each step clearly:

**STEP 1 — PLAN**
State what the code is meant to do and outline your analysis strategy.

**STEP 2 — ANALYZE**
Examine the code in detail, cross-referencing the retrieved bug patterns provided.

**STEP 3 — REPORT**
Produce a bug report in EXACTLY this format (do not deviate):

---
## Bug Report

**Confidence Score:** [0–100]%

### Bugs Found
- [Bug ID] | [Short description] | Severity: Low/Medium/High
  - Affected code: `<snippet>`
  - Suggested fix: `<fix>`

(Write "No bugs found." if the code is clean.)

### Code Summary
[1–2 sentences on what the code does.]

### Overall Assessment
[1–2 sentences on whether the code is safe to use as-is.]
---

Be precise. Do not add commentary outside this format."""


def analyze_code(code: str) -> dict:
    """
    Run the full agentic pipeline on a code snippet.
    Returns a dict: {raw, confidence, bugs, steps, error}
    """
    # Guardrails
    safe, reason = check_guardrails(code)
    if not safe:
        return {"error": reason, "bugs": [], "confidence": 0, "raw": "", "steps": []}

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "error": "ANTHROPIC_API_KEY not set. Add it to your .env file.",
            "bugs": [], "confidence": 0, "raw": "", "steps": [],
        }

    # Step 1: RAG retrieval
    logger.info("agent | step=1 | retrieving bug patterns")
    patterns = retrieve_relevant_patterns(code, top_k=3)
    rag_context = format_context(patterns)
    logger.info(f"agent | step=1 | retrieved={len(patterns)} patterns")

    # Step 2 + 3: Claude
    logger.info("agent | step=2-3 | calling Claude")
    client = anthropic.Anthropic(api_key=api_key)

    user_msg = (
        f"{rag_context}\n\n"
        f"## Code to Analyze\n```python\n{code}\n```\n\n"
        "Follow the 3-step process (Plan → Analyze → Report) and produce a complete bug report."
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1800,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text
        result = _parse_report(raw)
        log_analysis(code, result)
        logger.info(f"agent | complete | confidence={result['confidence']}%")
        return result

    except anthropic.AuthenticationError:
        return {
            "error": "Invalid API key. Check ANTHROPIC_API_KEY in your .env file.",
            "bugs": [], "confidence": 0, "raw": "", "steps": [],
        }
    except Exception as exc:
        logger.error(f"agent | error | {exc}")
        return {"error": str(exc), "bugs": [], "confidence": 0, "raw": "", "steps": []}


def _parse_report(raw: str) -> dict:
    """Extract structured fields from Claude's formatted response."""
    confidence = 0
    for line in raw.splitlines():
        if "confidence score" in line.lower():
            nums = re.findall(r"\d+", line)
            if nums:
                confidence = min(int(nums[0]), 100)
            break

    bugs = []
    in_bugs = False
    for line in raw.splitlines():
        low = line.strip().lower()
        if "### bugs found" in low:
            in_bugs = True
            continue
        if in_bugs and low.startswith("###"):
            break
        if in_bugs and line.strip().startswith("-"):
            bugs.append(line.strip("- ").strip())

    steps = []
    for label in ("STEP 1", "STEP 2", "STEP 3"):
        idx = raw.find(f"**{label}")
        if idx != -1:
            next_idx = raw.find("**STEP", idx + 5)
            chunk = raw[idx: next_idx if next_idx != -1 else idx + 600]
            steps.append(chunk.strip())

    return {"raw": raw, "confidence": confidence, "bugs": bugs, "steps": steps, "error": ""}
