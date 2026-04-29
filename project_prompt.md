# Game Glitch Investigator — Full Project Prompt

## Project Overview

A Python + Streamlit number-guessing game whose original AI-generated code contained deliberate bugs. The assignment is to:
1. Play the broken game and find the bugs.
2. Fix the bugs.
3. Refactor the logic out of `app.py` into `logic_utils.py`.
4. Run `pytest` and make all tests pass.
5. Fill in `reflection.md` with a post-mortem.

---

## Tech Stack & Dependencies (`requirements.txt`)

```
streamlit>=1.21.0
altair<5
pytest
```

---

## File Structure

```
project-root/
├── app.py                     # Main Streamlit app (all logic is here)
├── logic_utils.py             # Stub — all 4 functions raise NotImplementedError
├── tests/
│   └── test_game_logic.py     # pytest test suite (imports from logic_utils)
├── requirements.txt
├── README.md
└── reflection.md
```

---

## `app.py` — Complete Logic

### 1. `get_range_for_difficulty(difficulty: str) -> (int, int)`

Returns `(low, high)` inclusive range for the given difficulty string.

| difficulty    | low | high |
|---------------|-----|------|
| `"Easy"`      | 1   | 20   |
| `"Normal"`    | 1   | 50   |
| `"Hard"`      | 1   | 100  |
| anything else | 1   | 100  |

**Bugs in original (pre-fix):** Easy was 1–50, Normal was 1–100, Hard was 1–50 — the ranges were wrong/swapped.

---

### 2. `parse_guess(raw: str) -> (bool, int|None, str|None)`

Parses the raw text-input string from the UI.

Returns a 3-tuple `(ok, value, error_message)`.

| Input | Returns |
|-------|---------|
| `None` | `(False, None, "Enter a guess.")` |
| `""` (empty string) | `(False, None, "Enter a guess.")` |
| string containing `"."` | converts via `int(float(raw))`, returns `(True, int_value, None)` |
| valid integer string | `(True, int(raw), None)` |
| non-numeric string | `(False, None, "That is not a number.")` — catches any `Exception` |

---

### 3. `check_guess(guess, secret) -> (str, str)`

Returns a 2-tuple `(outcome, message)`.

| Condition | outcome | message |
|-----------|---------|---------|
| `guess == secret` | `"Win"` | `"🎉 Correct!"` |
| `guess > secret` | `"Too High"` | `"📈 Go lower!"` |
| `guess < secret` | `"Too Low"` | `"📉 Go higher!"` |
| `TypeError` fallback | uses string comparison on `str(guess)` vs `secret` | same outcome labels but uppercase `"Go LOWER!"` / `"Go HIGHER!"` |

**Bugs in original (pre-fix):** The hints were inverted — `guess > secret` said "Go higher" and `guess < secret` said "Go lower".

---

### 4. `update_score(current_score: int, outcome: str, attempt_number: int) -> int`

Returns the updated score.

| outcome | condition | effect |
|---------|-----------|--------|
| `"Win"` | always | `points = 100 - 10 * (attempt_number + 1)`, floored at `10`; adds `points` to score |
| `"Too High"` | `attempt_number % 2 == 0` | `+5` (bug — rewards wrong guesses) |
| `"Too High"` | `attempt_number % 2 != 0` | `-5` |
| `"Too Low"` | always | `-5` |
| anything else | — | unchanged |

**Note:** The `+5` on even-attempt "Too High" guesses is a known bug in the scorer — it awards points for wrong guesses.

---

## Difficulty & Attempt Limits

```python
attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
```

---

## Streamlit Session State Variables

| Key | Type | Initial value | Reset on New Game |
|-----|------|---------------|-------------------|
| `st.session_state.secret` | `int` | `random.randint(low, high)` | regenerated |
| `st.session_state.attempts` | `int` | `1` | reset to `0` |
| `st.session_state.score` | `int` | `0` | reset to `0` |
| `st.session_state.status` | `str` | `"playing"` | reset to `"playing"` |
| `st.session_state.history` | `list` | `[]` | reset to `[]` |

**State bug (pre-fix):** The secret was not stored in `session_state` initially, so every Streamlit rerun (triggered by any button click) regenerated the secret number, making the game unwinnable.

---

## UI Layout

```
Sidebar:
  - "Settings" header
  - Difficulty selectbox: ["Easy", "Normal", "Hard"], default index 1 (Normal)
  - Caption: "Range: {low} to {high}"
  - Caption: "Attempts allowed: {attempt_limit}"

Main:
  - Title: "🎮 Game Glitch Investigator"
  - Caption: "An AI-generated guessing game. Something is off."
  - Subheader: "Make a guess"
  - Info box: "Guess a number between {low} and {high}. Attempts left: {attempt_limit - attempts}"
  - Expander "Developer Debug Info":
      secret, attempts, score, difficulty, history
  - Form "guess_form":
      - Text input: key=f"guess_input_{difficulty}", placeholder="Type a number and press Enter"
      - Submit button: "Submit Guess 🚀"
  - 3 columns:
      col1: "New Game 🔁" button
      col2: "Show hint" checkbox (default True)
      col3: empty
  - Divider
  - Caption: "Built by an AI that claims this code is production-ready."
```

---

## Game Flow (Execution Order Each Rerun)

1. `st.set_page_config` and title/caption rendered.
2. Sidebar rendered with difficulty selectbox and captions.
3. `attempt_limit` and `(low, high)` computed from current `difficulty`.
4. Session state keys initialized if they don't already exist.
5. "Make a guess" subheader, info box, debug expander, form, and buttons rendered.
6. **New Game button handler:** if clicked → reset `attempts=0`, `score=0`, `status="playing"`, regenerate `secret`, clear `history`, show success toast, call `st.rerun()`.
7. **Status gate:** if `status != "playing"` → show won or lost message, call `st.stop()` (halts further execution).
8. **Submit handler:** if form submitted:
   - Increment `attempts += 1`
   - Call `parse_guess(raw_guess)`
   - If invalid: append raw string to history, show `st.error(err)`
   - If valid: append `guess_int` to history, call `check_guess`, optionally show hint with `st.warning(message)`, call `update_score`, check for win/loss and update `status`
9. If win: `st.balloons()`, set `status="won"`, show success message with secret and final score.
10. If out of attempts: set `status="lost"`, show error message with secret and score.

---

## `logic_utils.py` — Stub (Student Must Implement)

All four functions exist but raise `NotImplementedError`:

```python
def get_range_for_difficulty(difficulty: str): ...
def parse_guess(raw: str): ...
def check_guess(guess, secret): ...
def update_score(current_score: int, outcome: str, attempt_number: int): ...
```

---

## `tests/test_game_logic.py`

Imports `check_guess` from `logic_utils` (NOT from `app.py`). The tests assert on the **outcome string only** (not the full tuple):

```python
def test_winning_guess():
    result = check_guess(50, 50)
    assert result == "Win"           # expects string, not tuple

def test_guess_too_high():
    result = check_guess(60, 50)
    assert result == "Too High"

def test_guess_too_low():
    result = check_guess(40, 50)
    assert result == "Too Low"
```

**Key discrepancy:** `app.py`'s `check_guess` returns a 2-tuple `(outcome, message)`. The tests assert on just the string. So the student must implement `logic_utils.check_guess` to return **only the outcome string**, not the tuple — or adjust the tests accordingly.

---

## Bugs Found (Documented in `reflection.md`)

1. **Hints inverted** — "Too Low" said go lower, "Too High" said go higher.
2. **Enter key submission broken** — text input said "Press Enter to apply" but didn't submit the form.
3. **Score awarded on wrong guesses** — `+5` was given on even-attempt incorrect "Too High" guesses.
4. **Difficulty ranges wrong** — Normal had 1–100, Hard had 1–50 (should be swapped to match difficulty intent).
5. **New Game then Submit broken** — after game over, clicking New Game made the submit button stop working (state wasn't fully reset).
6. **Secret number changed on every rerun** — not stored in session state, so every button click regenerated it.

---

## Fixed Bugs (current `app.py` on `main` branch, commit `7c61ac6`)

- `get_range_for_difficulty` now returns correct ranges per difficulty.
- `check_guess` hints are now correct (`guess > secret` → "Go lower").
- Session state is properly initialized with `if "key" not in st.session_state` guards.
- New Game resets `attempts` to `0` and calls `st.rerun()`.
- The form's text input key is `f"guess_input_{difficulty}"` (keyed to difficulty to force refresh on difficulty change, which also enables Enter-key submission through the form).

---

## Source Code

### `app.py`

```python
import random
import streamlit as st

def get_range_for_difficulty(difficulty: str):
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 50
    if difficulty == "Hard":
        return 1, 100
    return 1, 100


def parse_guess(raw: str):
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    if guess == secret:
        return "Win", "🎉 Correct!"

    try:
        if guess > secret:
            return "Too High", "📈 Go lower!"
        else:
            return "Too Low", "📉 Go higher!"
    except TypeError:
        g = str(guess)
        if g == secret:
            return "Win", "🎉 Correct!"
        if g > secret:
            return "Too High", "📈 Go LOWER!"
        return "Too Low", "📉 Go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int):
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

if "attempts" not in st.session_state:
    st.session_state.attempts = 1

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

st.subheader("Make a guess")

st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

with st.form("guess_form"):
    raw_guess = st.text_input(
        "Enter your guess:",
        key=f"guess_input_{difficulty}",
        placeholder="Type a number and press Enter"
    )
    submit = st.form_submit_button("Submit Guess 🚀")

col1, col2, col3 = st.columns(3)
with col1:
    new_game = st.button("New Game 🔁")
with col2:
    show_hint = st.checkbox("Show hint", value=True)
with col3:
    st.empty()

if new_game:
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.secret = random.randint(low, high)
    st.session_state.history = []
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    st.session_state.attempts += 1

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.history.append(guess_int)

        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
```

---

### `logic_utils.py` (starter stub)

```python
def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")
```

---

### `tests/test_game_logic.py`

```python
from logic_utils import check_guess

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"
```

---

## How to Run

```bash
pip install -r requirements.txt
python -m streamlit run app.py   # run the app
pytest                           # run tests (requires logic_utils.py to be implemented)
```
