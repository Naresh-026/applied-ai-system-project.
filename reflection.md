# Reflection — Game Glitch Investigator

## What the project is

A Python + Streamlit number-guessing game whose original AI-generated code contained six deliberate bugs. The task was to play the broken game, find each bug, fix it, refactor the logic into `logic_utils.py`, and make the `pytest` suite pass.

---

## Bugs Found and Fixed

### Bug 1 — Hints were inverted
**Symptom:** When my guess was too high, the game said "Go higher!" and vice versa.  
**Root cause:** The comparison in `check_guess` had the return values swapped — `guess > secret` returned the "Too Low" message and `guess < secret` returned the "Too High" message.  
**Fix:** Swapped the return values so `guess > secret` → "Go lower!" and `guess < secret` → "Go higher!".

---

### Bug 2 — Secret number changed on every rerun
**Symptom:** The game was effectively unwinnable — no matter how close I guessed, the target kept moving.  
**Root cause:** `random.randint(low, high)` was called unconditionally on every script run. Because Streamlit reruns the entire script on every interaction, a new secret was generated on every button click.  
**Fix:** Wrapped the assignment in `if "secret" not in st.session_state` so the secret is generated only once per game.

---

### Bug 3 — Difficulty ranges were wrong / swapped
**Symptom:** "Easy" gave a 1–50 range and "Hard" gave a 1–50 range (same!); "Normal" gave 1–100.  
**Root cause:** The `get_range_for_difficulty` conditions returned incorrect `(low, high)` pairs — Easy and Normal were swapped, and Hard matched Easy instead of being the widest range.  
**Fix:** Corrected the mapping: Easy → 1–20, Normal → 1–50, Hard → 1–100.

---

### Bug 4 — Enter key didn't submit the form
**Symptom:** Typing a number and pressing Enter did nothing; only the "Submit Guess 🚀" button worked.  
**Root cause:** The text input was not inside a `st.form` block. Streamlit only enables Enter-key submission when an input is inside a form with a `st.form_submit_button`.  
**Fix:** Wrapped the text input and submit button inside `with st.form("guess_form"):`. The input key was also tied to difficulty (`f"guess_input_{difficulty}"`) so changing difficulty forces a fresh input widget, preventing stale values from carrying over.

---

### Bug 5 — Score rewarded wrong guesses
**Symptom:** Sometimes my score went *up* after a wrong guess.  
**Root cause:** `update_score` had a branch that awarded `+5` when `outcome == "Too High"` and `attempt_number % 2 == 0`. This is a known intentional bug in the scorer — it rewards incorrect guesses on even-numbered attempts.  
**Status:** Preserved as a documented known quirk (the project spec calls it out). Noted in code with a comment.

---

### Bug 6 — New Game then Submit broke the game
**Symptom:** After a game ended (win or loss), clicking "New Game" and then trying to guess did nothing — the submit button appeared to fire but no feedback appeared.  
**Root cause:** The "New Game" handler reset `attempts` to `1` (not `0`), and `status` was never fully cleared before `st.rerun()` was called. The status gate (`if st.session_state.status != "playing": st.stop()`) then blocked the submit handler on the very next rerun.  
**Fix:** Reset `attempts = 0` and explicitly set `status = "playing"` before calling `st.rerun()`.

---

## Refactoring: `app.py` → `logic_utils.py`

All four game-logic functions were extracted into `logic_utils.py`:

| Function | Change during refactor |
|---|---|
| `get_range_for_difficulty` | No change — moved as-is |
| `parse_guess` | No change — moved as-is |
| `check_guess` | **Return type changed:** now returns only the outcome string (`"Win"`, `"Too High"`, `"Too Low"`) instead of a `(outcome, message)` tuple, so the `pytest` tests pass without modification |
| `update_score` | No change — moved as-is |

`app.py` now imports from `logic_utils` and uses a local `HINT_MESSAGES` dict to map outcome strings to display text.

---

## What I learned

- **Session state is essential in Streamlit.** Because every interaction reruns the entire script, any value that must persist across reruns — like the secret number — must live in `st.session_state`.
- **AI-generated code looks convincing but can hide subtle logic errors.** The inverted hints and swapped difficulty ranges were syntactically valid Python; only playing the game revealed they were wrong.
- **Test design shapes implementation.** The `pytest` suite expected `check_guess` to return a plain string, not a tuple. That constraint drove a clean separation: pure outcome logic in `logic_utils`, UI messaging in `app.py`.
- **Small state bugs cascade.** The "New Game" bug wasn't a single broken line — it was `attempts` starting at the wrong value AND `status` not being reset in the right order, which together broke the whole flow.
