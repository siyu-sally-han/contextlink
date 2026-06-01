# CODING_AGENT_SESSION_SUMMARY.md

## ContextLink — Human-in-the-Loop Entity Matching for Research Data

---

## 1. Project Overview

**ContextLink** is a Streamlit prototype that helps social network researchers review possible duplicate people in messy survey data. It uses entirely synthetic data and is not connected to any real or private dataset. The session produced a fully working local app, which I ran and tested at `http://localhost:8501`.

The motivation comes directly from a sociology research assistant workflow: human-entered relationship records accumulate ambiguous names, initials, role labels, and spelling variants, and automatic merging of these entries without human review risks corrupting the network data. The goal of ContextLink is not to merge records automatically, but to surface likely duplicates in priority order and let the researcher make every final call.

The app presents candidate pairs one at a time with a confidence score, name similarity score, context similarity score, a tier label (HIGH / MEDIUM / LOW / UNCERTAIN), per-signal reason codes, and safety warnings for risky edge cases. Researchers decide each pair with Approve, Reject, or Needs Review, optionally add a note, and export all decisions as CSV.

**Stack:** Python 3, Streamlit, pandas, rapidfuzz, Faker  
**Data:** 40 fully synthetic survey entries across 10 named edge-case clusters  
**Files:** `app.py`, `engine/matcher.py`, `data/synthetic.py`, `state/review_store.py`, `requirements.txt`

---

## 2. Why I'm Proud of This Coding Agent Session

This session is not just about the code that was produced — it is about how I drove it. I set a principled constraint from the start (synthetic data only, no real research data), required the agent to build incrementally with my approval at each step, caught two functional bugs myself by running the app locally, and requested a read-only audit before allowing any edge-case changes.

The session demonstrates that I can:
- Architect a multi-component prototype with clear separation of concerns
- Identify real UI bugs through hands-on testing, not just code review
- Apply skepticism about AI-generated code before accepting it
- Approve only the smallest safe changes rather than letting the agent rewrite things

---

## 3. Step-by-Step Session Progression

| Step | What I Asked For | What Was Produced |
|------|-----------------|-------------------|
| 1 | Propose the project structure only — no code | Architecture proposal with file roles explained |
| 2 | Confirm revised structure; confirm synthetic-data-only and English-only constraints | Architecture confirmed with explicit guarantees |
| 3 | Generate synthetic data only (`data/synthetic.py`) | 40 entries across 10 edge-case clusters with false-positive risks documented |
| 4 | Implement the matching engine only (`engine/matcher.py`) | Name normalization, context similarity, confidence scoring, safety caps, smoke test |
| 5 | Build the Streamlit app (`app.py`, `state/review_store.py`) | Full review UI with sidebar stats, comparison cards, decision buttons, CSV export |
| 6 | Fix the Reject button crash (bug I found) | Streamlit session state bug identified and fixed with a deferred-clear flag pattern |
| 7 | Fix the button highlight issue (UI bug I found) | Per-pair `_selected_decision` state added; button `type` made dynamic |
| 7A | Audit edge-case handling — read only, no changes yet | Detailed audit report: what works, what is missing, three smallest safe changes proposed |
| 7B | Implement only the approved minimal changes | Safety flags decoupled from caps; per-tier rationale added; tier counts added to sidebar |

---

## 4. Key Prompts and Decisions I Made

**Synthetic data constraint**  
I explicitly required that no real or private research data be used anywhere — not in the dataset, not in variable names, not in example outputs. This was stated in Step 2 and held throughout.

**Step-by-step gating**  
Rather than asking the agent to generate the full project at once, I approved each step individually. This kept the scope clear and let me review each layer before the next was built on top of it.

**Edge-case design in the synthetic data**  
I specified the exact edge-case categories I wanted: family role labels (Mom/Mama/Mother), initials (B, LR), abbreviations (A. Chen), nicknames (Mike/Mikey/Michael), title prefixes (Dr./Prof./Uncle), spelling variations (Sara/Sarah), and same-name-different-person (Chris Park × 2). I also required the dataset to include intentional false positives so the safety logic would have something to guard against.

**Running the app locally and fixing the launch command**  
The standard `streamlit run app.py` command was not found in my shell PATH. I resolved this by using `python3 -m streamlit run app.py` instead.

**Audit before changes**  
After the first working version was complete, I did not ask the agent to improve it immediately. I first requested a read-only audit of the edge-case handling, reviewed the findings, and then approved only three specific minimal changes — nothing more.

**Restricting scope at every step**  
When the agent proposed changes, I consistently scoped them down. For example, I approved decoupling safety flags from safety caps, a per-tier rationale sentence, and tier counts in the sidebar — and explicitly excluded any redesign, rescoring, or session state changes.

---

## 5. Bugs I Found and Debugged

### Bug 1 — Reject button crash (`StreamlitAPIException`)

**How I found it:** I ran the app locally and clicked the Reject button. The app crashed with:

```
StreamlitAPIException: st.session_state.reviewer_note cannot be modified
after the widget with key reviewer_note is instantiated.
```

**Root cause:** In Streamlit, once a widget is rendered with a `key`, that key is owned by the widget for the rest of the script run. The original `record_decision` function tried to reset `st.session_state.reviewer_note = ""` after the `st.text_area` had already been instantiated — this violates Streamlit's ownership model.

**Fix:** A deferred-clear flag (`_clear_note`) is set in `record_decision` instead of writing directly to the widget key. The actual reset (`st.session_state.reviewer_note = ""`) happens at the top of the next rerun, before the `text_area` widget is instantiated.

### Bug 2 — Approve button always appeared highlighted

**How I found it:** After fixing Bug 1, I noticed that the Approve button had a filled/active appearance on every candidate pair, even immediately after clicking Reject or Needs Review.

**Root cause:** The Approve button had `type="primary"` hardcoded unconditionally. Streamlit's `primary` type gives a button its filled style regardless of what the user clicked. The other two buttons had no `type` specified, so they always appeared unselected.

**Fix:** A `_selected_decision` dict in session state maps each `(id_a, id_b)` pair key to the last decision made for that pair. Each button's `type` is computed dynamically: `"primary"` if `_selected == "THIS_DECISION"`, `"secondary"` otherwise. Before any decision is made for a new candidate, all three buttons render as secondary (no highlight). Decisions do not carry over between candidates because the key is pair-specific.

---

## 6. Final Prototype

The working prototype handles all of the following cases correctly:

| Case | Behavior |
|------|----------|
| Mom / Mama / Mother | HIGH confidence — family role canonical match |
| B / Brandon | MEDIUM — single-initial safety flag always shown |
| LR / Lily Ren | MEDIUM — two-letter-initials safety flag always shown |
| Alex Chen / A. Chen | HIGH — abbreviated token match with strong context |
| Mike / Michael / Mikey | HIGH — nickname group match |
| Dr. Lee / Prof. Lee / Lee | HIGH — title prefix stripped, exact match |
| Sara / Sarah Johnson | HIGH — spelling variation, same city |
| Chris Park × 2 (different cities) | LOW — identical name, different locations safety flag |
| Uncle Wang / Mr. Wang / Wang | HIGH — title prefix stripped, same location |

The UI shows:
- Side-by-side comparison cards for Entry A and Entry B
- Four score metrics: confidence, name similarity, context similarity, tier badge
- Signal breakdown (Name / Context / Safety sections) in an expandable panel
- A per-tier rationale sentence explaining what the tier means for the reviewer's decision
- Approve / Reject / Needs Review buttons (only the selected one is highlighted)
- Optional reviewer note, persisted with each decision
- Sidebar stats: entry count, pair count, reviewed/unreviewed, progress bar, tier counts (HIGH / MEDIUM / LOW / UNCERTAIN)
- Reviewed decisions table with color-coded decisions and CSV export

---

## 7. What This Demonstrates About My AI Coding Ability

**I treat AI output as a draft, not a final answer.**  
I ran the app, found two bugs myself, diagnosed both before asking for a fix, and described the expected behavior precisely in my bug reports.

**I use incremental approval to maintain control.**  
By gating each step, I avoided the common failure mode of asking for everything at once and getting a large codebase I did not fully understand. Each component was reviewed before the next was built on it.

**I can read and evaluate AI-generated code for correctness.**  
Before approving the edge-case improvements, I asked for a read-only audit and reviewed the findings — including identifying that safety flags were not appearing for B/Brandon and LR/Lily Ren even though the logic looked correct at first glance.

**I set appropriate boundaries for a research prototype.**  
I consistently declined to add features beyond what the task required, kept the data entirely synthetic, and resisted scope creep (no automatic merging, no real-data connectors, no unnecessary abstraction layers).

**I understand the human-in-the-loop principle, not just the code.**  
The core design decision — that the system scores and explains, but never decides — was set in Step 2 and enforced throughout. Every architecture and UI choice supports that principle.

---

*This prototype was built in a single guided coding session using Claude Code (claude-sonnet-4-6). All data is synthetic. No real or private research data was used at any point.*
