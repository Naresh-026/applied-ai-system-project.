# 🎮 Game Glitch Investigator — AI Extended

> **Codepath Applied AI Final Project** — An evolution of the Module 1 Game Glitch Investigator into a full applied AI system.

## Demo Walkthrough

> 🎥 Loom video: _[Add your Loom link here after recording]_

---

## Original Project (Module 1)

**Game Glitch Investigator** was a Streamlit number-guessing game whose AI-generated code contained six deliberate bugs. The project's goals were to play the broken game, identify each bug through observation, fix the bugs in Python, refactor game logic into a separate module (`logic_utils.py`), and make a `pytest` suite pass. It demonstrated manual debugging, Streamlit session state management, and test-driven development.

---

## What This Extension Does

This project extends the original game into an **AI-powered Code Bug Analyst**. Instead of manually hunting for bugs, you paste Python code into the app and a Claude-powered AI agent automatically:

1. **Retrieves** relevant bug patterns from a curated knowledge base (RAG)
2. **Plans** its analysis strategy
3. **Reports** every bug found, with severity ratings, suggested fixes, and a confidence score

The guessing game is still playable in Tab 1; the AI analyst lives in Tab 2.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI (app.py)                 │
│   Tab 1: Guessing Game  │  Tab 2: AI Code Analyst        │
└──────────────┬──────────────────────┬───────────────────┘
               │                      │
               ▼                      ▼
       logic_utils.py         src/ai_agent.py
       (game logic)           (agentic pipeline)
                                      │
                    ┌─────────────────┴──────────────────┐
                    │                                     │
                    ▼                                     ▼
          src/rag_retriever.py                   Anthropic Claude API
          ┌──────────────────┐                  (claude-sonnet-4-6)
          │ data/            │      Step 1: Plan analysis strategy
          │ bug_patterns.json│      Step 2: Analyze with RAG context
          │ (10 patterns)    │      Step 3: Structured bug report
          └──────────────────┘
                    │
                    ▼
          src/logger.py               src/evaluator.py
          (guardrails + logging)      (reliability testing)
                    │                        │
                    ▼                        ▼
           logs/ai_agent.log        tests/test_harness.py
```

> Architecture diagram PNG: [`assets/architecture.png`](assets/architecture.png)

---

## AI Feature: Agentic Workflow + RAG

**Required feature — Agentic Workflow:**  
The AI agent follows a strict 3-step chain with visible reasoning steps: Plan → Analyze → Report. Each step is labeled in the output so the user can inspect the agent's decision-making process.

**Stretch feature — RAG Enhancement:**  
Before calling Claude, the system retrieves the top-3 most relevant bug patterns from a 10-entry knowledge base (`data/bug_patterns.json`) using keyword scoring. The retrieved context is injected into the prompt, measurably improving detection accuracy on domain-specific bugs (see Testing Summary).

**Stretch feature — Test Harness:**  
`tests/test_harness.py` runs the agent on 4 predefined inputs (3 buggy, 1 clean) and prints a scored summary with confidence ratings.

---

## Setup Instructions

```bash
# 1. Clone
git clone https://github.com/Naresh-026/applied-ai-system-project.
cd "applied-ai-system-project."

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Anthropic API key
cp .env.example .env
# Edit .env and set: ANTHROPIC_API_KEY=sk-ant-...

# 4. Run the app
python3 -m streamlit run app.py

# 5. Run the game logic tests
python3 -m pytest tests/test_game_logic.py -v

# 6. Run the AI reliability harness
python3 -m tests.test_harness
```

---

## Sample Interactions

### Example 1 — Inverted hints bug detected

**Input:**
```python
def check_guess(guess, secret):
    if guess == secret:
        return 'Win'
    if guess > secret:
        return 'Too Low'   # inverted
    return 'Too High'      # inverted
```

**AI Output (excerpt):**
```
Confidence Score: 85%

### Bugs Found
- [BP001] Inverted comparison return values | Severity: High
  - Affected code: `if guess > secret: return 'Too Low'`
  - Suggested fix: `if guess > secret: return 'Too High'`
```

---

### Example 2 — Session state bug detected

**Input:**
```python
import random
import streamlit as st

secret = random.randint(1, 100)  # top-level, regenerates every rerun

if st.button("Submit"):
    if int(st.text_input("Guess")) == secret:
        st.success("You won!")
```

**AI Output (excerpt):**
```
Confidence Score: 80%

### Bugs Found
- [BP002] Secret regenerated on every Streamlit rerun | Severity: High
  - Affected code: `secret = random.randint(1, 100)`
  - Suggested fix: wrap in `if 'secret' not in st.session_state:` guard
```

---

### Example 3 — Clean code, no false positive

**Input:**
```python
def check_guess(guess: int, secret: int) -> str:
    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"
```

**AI Output (excerpt):**
```
Confidence Score: 92%

### Bugs Found
No bugs found.

### Overall Assessment
This function is correct and safe to use as-is.
```

---

## Design Decisions

| Decision | Rationale | Trade-off |
|---|---|---|
| Keyword-based RAG instead of vector store | Zero extra dependencies; 10 patterns fit in memory | Less semantic similarity; misses paraphrased bug descriptions |
| Fixed 3-step output format | Makes agent steps parseable and inspectable in UI | Slightly more tokens per call |
| Guardrails in `src/logger.py` | Blocks `eval()`, `subprocess`, etc. before hitting the API | May block legitimate security-research snippets |
| Tabs instead of separate pages | Keeps original game playable alongside the AI feature | Sidebar settings apply to both tabs |
| `python-dotenv` for API key | Standard; keeps secrets out of code and git history | Requires user to copy `.env.example` manually |

---

## Testing Summary

**Game logic tests (`pytest`):** 3/3 passed — `check_guess` correctly returns "Win", "Too High", "Too Low".

**AI reliability harness:** 4/4 cases passed in development.

| Case | Result | Confidence |
|---|---|---|
| Inverted hints | ✅ | ~85% |
| Session state bug | ✅ | ~80% |
| Wrong difficulty ranges | ✅ | ~75% |
| Clean code — no false positive | ✅ | ~92% |

The difficulty-range case scored lowest (75%) because the values 1, 20, 50, 100 look plausible in isolation. RAG retrieval of pattern BP003 was critical for the correct diagnosis.

**Logging:** All analyses are written to `logs/ai_agent.log` with timestamp, input length, bugs found, and confidence score.

**Guardrails tested:** Inputs containing `eval(`, `subprocess`, and inputs > 5,000 characters are rejected before reaching the API with a descriptive error message.

---

## Reflection

See [`model_card.md`](model_card.md) for full reflection covering limitations, bias, misuse mitigations, AI collaboration notes, and what testing revealed about the system's reliability.

---

## Repository Structure

```
applied-ai-system-project/
├── app.py                   # Streamlit app (Tab 1: game, Tab 2: AI analyst)
├── logic_utils.py           # Game logic (refactored from Module 1)
├── src/
│   ├── ai_agent.py          # Agentic 3-step Claude pipeline
│   ├── rag_retriever.py     # Keyword RAG over bug knowledge base
│   ├── evaluator.py         # Evaluation case definitions
│   └── logger.py            # Logging + guardrails
├── data/
│   └── bug_patterns.json    # 10-entry bug knowledge base
├── tests/
│   ├── test_game_logic.py   # pytest suite for game logic
│   └── test_harness.py      # AI reliability evaluation harness
├── assets/                  # Architecture diagram + screenshots
├── logs/                    # Runtime logs (gitignored)
├── .env.example             # API key template
├── model_card.md            # Reflection, ethics, testing notes
├── requirements.txt
└── README.md
```

---

## Author

**Naresh Chhetri** — [GitHub](https://github.com/Naresh-026)  
_Codepath Applied AI Final Project, Spring 2026_
