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
        logger.warning("agent | auth error — falling back to rule-based analyser")
        return _rule_based_fallback(code, patterns)
    except anthropic.BadRequestError as exc:
        # Catches "credit balance too low" and similar billing errors
        if "credit" in str(exc).lower() or "balance" in str(exc).lower():
            logger.warning("agent | no credits — falling back to rule-based analyser")
            return _rule_based_fallback(code, patterns)
        logger.error(f"agent | error | {exc}")
        return _rule_based_fallback(code, patterns)
    except Exception as exc:
        logger.warning(f"agent | api unavailable ({exc}) — falling back to rule-based analyser")
        return _rule_based_fallback(code, patterns)


def _rule_based_fallback(code: str, patterns: list[dict]) -> dict:
    """
    Offline fallback: match retrieved RAG patterns against the code via keyword
    scoring. Returns the same dict shape as the Claude path.
    """
    logger.info("agent | fallback | running rule-based analysis")
    code_lower = code.lower()
    matched = []

    for p in patterns:
        hits = [kw for kw in p["keywords"] if kw.lower() in code_lower]
        if len(hits) >= 2:  # require at least 2 keyword hits to flag a pattern
            matched.append((len(hits), p))

    matched.sort(key=lambda x: x[0], reverse=True)

    if matched:
        confidence = min(50 + 8 * len(matched), 80)  # cap at 80 — fallback is less certain
        bugs_lines = []
        report_bugs = []
        for _, p in matched:
            line = (
                f"- [{p['id']}] {p['description']} | Severity: High\n"
                f"  - Buggy pattern: `{p['example_bug']}`\n"
                f"  - Suggested fix: `{p['example_fix']}`"
            )
            bugs_lines.append(line)
            report_bugs.append(f"[{p['id']}] {p['description']}")

        bugs_section = "\n".join(bugs_lines)
        raw = (
            f"**STEP 1 — PLAN** _(rule-based fallback mode — no API credits)_\n"
            f"Scanning code against {len(patterns)} retrieved bug patterns from the knowledge base.\n\n"
            f"**STEP 2 — ANALYZE**\n"
            f"Keyword matching identified {len(matched)} potential issue(s).\n\n"
            f"**STEP 3 — REPORT**\n\n"
            f"---\n## Bug Report\n\n"
            f"**Confidence Score:** {confidence}%\n\n"
            f"### Bugs Found\n{bugs_section}\n\n"
            f"### Code Summary\n"
            f"Code analysed via offline rule-based engine using {len(patterns)} RAG-retrieved patterns.\n\n"
            f"### Overall Assessment\n"
            f"Found {len(matched)} likely issue(s). Add API credits to enable full Claude analysis for deeper insights.\n"
            f"---"
        )
    else:
        confidence = 60
        raw = (
            f"**STEP 1 — PLAN** _(rule-based fallback mode — no API credits)_\n"
            f"Scanning code against {len(patterns)} retrieved bug patterns.\n\n"
            f"**STEP 2 — ANALYZE**\nNo strong keyword matches found.\n\n"
            f"**STEP 3 — REPORT**\n\n"
            f"---\n## Bug Report\n\n"
            f"**Confidence Score:** {confidence}%\n\n"
            f"### Bugs Found\nNo bugs found.\n\n"
            f"### Code Summary\nNo matching bug patterns detected in offline mode.\n\n"
            f"### Overall Assessment\n"
            f"Code appears clean based on rule-based checks. Add API credits for a full Claude review.\n"
            f"---"
        )

    result = _parse_report(raw)
    result["fallback"] = True
    log_analysis(code, result)
    return result


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
