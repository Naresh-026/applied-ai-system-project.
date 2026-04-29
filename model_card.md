# Model Card — AI Code Bug Analyst

## Base Model

**Claude Sonnet 4.6** (`claude-sonnet-4-6`) by Anthropic, accessed via the Anthropic Messages API.  
No fine-tuning was applied. The model is steered through a structured system prompt that enforces a 3-step agentic workflow (Plan → Analyze → Report) and a fixed output format.

---

## System Overview

This system extends the *Game Glitch Investigator* (Codepath Module 1) into an applied AI system that automatically detects bugs in Python code. The AI agent combines retrieval-augmented generation (RAG) over a curated bug-pattern knowledge base with Claude's reasoning capabilities to produce structured, confidence-scored bug reports.

---

## Intended Use

- **Primary users:** Students and developers who want a second opinion on Python code quality.
- **Intended tasks:** Identifying logic errors, state management bugs, input validation gaps, and control-flow issues in short Python snippets (≤ 5,000 characters).
- **Out of scope:** Production security audits, large codebases, compiled languages, or malicious code analysis.

---

## Limitations and Biases

1. **Knowledge base is narrow.** The RAG system contains 10 patterns focused on Streamlit game bugs. Code from other domains may receive weak retrieval context, degrading analysis quality.
2. **No code execution.** The model reasons about code statically. Dynamic bugs (race conditions, environment-specific failures) are invisible to it.
3. **Confidence scores are self-reported.** Claude estimates its own confidence. This is not calibrated against ground truth and may be overconfident on unfamiliar patterns.
4. **Hallucination risk.** The model may invent plausible-sounding bug descriptions for code it has not seen before. All output should be reviewed by a human before acting on it.
5. **Language bias.** The system prompt and knowledge base are English-only. Code with non-English comments or identifiers may receive degraded analysis.
6. **Short snippet bias.** Analysis quality drops for snippets without enough context (e.g., a function body without its callers).

---

## Potential Misuse and Mitigations

| Risk | Mitigation |
|---|---|
| Submitting malicious/destructive code to probe the model | Guardrail in `src/logger.py` blocks patterns like `subprocess`, `eval()`, `os.system` |
| Using AI output as authoritative security verdict | Output labeled "Bug Report" not "Security Audit"; README warns against production use without human review |
| Overloading the API with automated bulk requests | 5,000-character input cap limits compute per call; no batch endpoint exposed |

---

## Testing Results

| Test Case | Result | Confidence | Notes |
|---|---|---|---|
| Inverted comparison hints | ✅ Pass | ~85% | Correctly identified swapped return values |
| Secret regenerated on rerun | ✅ Pass | ~80% | Flagged missing `session_state` guard |
| Wrong difficulty ranges | ✅ Pass | ~75% | Detected swapped range values |
| Clean code (no bugs) | ✅ Pass | ~90% | No false positives |

**Summary:** 4/4 eval cases passed in development testing. Average confidence: ~82%. The system struggled most with the difficulty-range case because the values (1, 20, 50, 100) look reasonable in isolation — the RAG retrieval of BP003 provided the critical context that tipped the analysis.

---

## AI Collaboration Reflection

**One instance where AI gave a helpful suggestion:**  
When I asked Claude to design the agentic workflow structure, it proactively suggested separating the RAG retrieval step from the analysis step and emitting visible "STEP 1 / STEP 2 / STEP 3" labels in the output. This made the reasoning chain transparent and directly enabled the "View agent reasoning steps" expander in the UI — a feature I had not originally planned but which significantly improves the demo.

**One instance where AI's suggestion was flawed:**  
Claude initially suggested using `chromadb` or `faiss` for the vector store component. This was technically sound but impractical: both require native binary dependencies that frequently break on Apple Silicon, and the overhead of a proper vector store is unjustified for a 10-document knowledge base. I replaced this with a simple keyword-scoring retriever in `src/rag_retriever.py`, which is faster, dependency-free, and sufficiently accurate for this scale.

---

## What Surprised Me During Testing

The most surprising finding was how much the **RAG context changed the output quality**. On the "difficulty range" test case, running Claude without retrieval produced a vague response ("the ranges seem unusual"). After injecting BP003 from the knowledge base, Claude immediately identified the specific swap and explained *why* Easy should be 1–20. This validated the RAG design choice and showed that a small, curated knowledge base can compensate for a model's lack of domain-specific memory.

---

## What This Project Taught Me About AI

Building this system reinforced three lessons: (1) **structure beats instructions** — a rigid output format (Bug Report → Confidence → Bugs Found → Summary) produces far more consistent, parseable results than asking the model to "be organized"; (2) **retrieval is cheap leverage** — 10 hand-written bug patterns produced measurable accuracy gains with zero training cost; (3) **guardrails are not optional** — even in a low-stakes student project, blocking dangerous input patterns and capping input size prevented a whole class of misuse scenarios without requiring any model changes.
