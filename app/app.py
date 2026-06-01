"""
app.py — ContextLink Streamlit review interface.
Human-in-the-loop entity matching for social network research data.
Synthetic data only; no real or private research data is used.
"""

from __future__ import annotations

import sys
import os

import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from data.synthetic import load_entries
from engine.matcher import generate_candidates
from state.review_store import ReviewStore


# ─── page configuration ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="ContextLink",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── styling ──────────────────────────────────────────────────────────────────

TIER_COLORS = {
    "HIGH":      ("#155724", "#d4edda"),   # (text, background)
    "MEDIUM":    ("#856404", "#fff3cd"),
    "LOW":       ("#721c24", "#f8d7da"),
    "UNCERTAIN": ("#383d41", "#e2e3e5"),
}

DECISION_COLORS = {
    "APPROVED":     ("#155724", "#d4edda"),
    "REJECTED":     ("#721c24", "#f8d7da"),
    "NEEDS_REVIEW": ("#856404", "#fff3cd"),
}

# Explains to the reviewer why human judgment is needed for each tier.
TIER_RATIONALE = {
    "HIGH":      "Strong name and context evidence — verify the details in both cards before approving.",
    "MEDIUM":    "Moderate evidence only — name or context signals are indirect. Do not approve without independent confirmation.",
    "LOW":       "Weak evidence — these entries likely refer to different people. Reject unless you have a clear reason to merge.",
    "UNCERTAIN": "Insufficient signals — the available data cannot confirm or deny a match. Use your judgment and add a note.",
}

st.markdown("""
<style>
/* ── badge chips ── */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.06em;
}
/* ── entry field rows ── */
.field-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6c757d;
    margin-top: 10px;
    margin-bottom: 1px;
}
.field-value {
    font-size: 0.92rem;
    color: #212529;
}
/* ── card section header ── */
.card-header {
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #adb5bd;
    margin-bottom: 6px;
}
.alter-name {
    font-size: 1.5rem;
    font-weight: 700;
    color: #212529;
    margin-bottom: 4px;
}
/* ── reason code list ── */
.reason-signal {
    font-size: 0.83rem;
    padding: 4px 0;
    color: #495057;
    border-bottom: 1px solid #f1f3f5;
    line-height: 1.45;
}
</style>
""", unsafe_allow_html=True)


# ─── data bootstrap ───────────────────────────────────────────────────────────

@st.cache_data
def _load_data() -> tuple[pd.DataFrame, list[dict]]:
    df         = load_entries()
    candidates = generate_candidates(df)
    return df, candidates


def _init_session() -> None:
    if "store" not in st.session_state:
        df, candidates = _load_data()
        st.session_state.store = ReviewStore(candidates)
        st.session_state.df    = df
    if "reviewer_note" not in st.session_state:
        st.session_state.reviewer_note = ""
    if "_selected_decision" not in st.session_state:
        # Maps (id_a, id_b) → decision string so each pair tracks its own highlight.
        st.session_state._selected_decision = {}


_init_session()
store: ReviewStore = st.session_state.store
df: pd.DataFrame   = st.session_state.df


# ─── helpers ──────────────────────────────────────────────────────────────────

def badge(text: str, text_color: str, bg_color: str) -> str:
    return (
        f'<span class="badge" '
        f'style="color:{text_color};background:{bg_color}">{text}</span>'
    )


def tier_badge(tier: str) -> str:
    tc, bg = TIER_COLORS.get(tier, ("#383d41", "#e2e3e5"))
    return badge(tier, tc, bg)


def lookup_entry(entry_id: str) -> dict:
    row = df[df["entry_id"] == entry_id]
    return row.iloc[0].to_dict() if not row.empty else {}


def record_decision(pair: dict, decision: str) -> None:
    note = st.session_state.get("reviewer_note", "")
    store.record(pair["id_a"], pair["id_b"], decision, note)
    # Track which button was selected for this specific pair so the highlight
    # is tied to the candidate, not carried over to the next one.
    st.session_state._selected_decision[(pair["id_a"], pair["id_b"])] = decision
    # Signal that the note should be cleared on the next rerun.
    # We cannot write to reviewer_note here because the text_area widget
    # that owns that key has already been rendered in this script run.
    st.session_state._clear_note = True
    st.rerun()


def render_entry_card(entry: dict, side_label: str) -> None:
    st.markdown(f'<div class="card-header">{side_label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="alter-name">{entry.get("alter_name", "—")}</div>', unsafe_allow_html=True)

    fields = [
        ("Entry ID",     entry.get("entry_id", "—")),
        ("Respondent",   entry.get("respondent_id", "—")),
        ("Relationship", entry.get("relationship_label", "—")),
        ("Tie type",     entry.get("tie_type", "—")),
        ("Location",     entry.get("location", "—")),
        ("Notes",        entry.get("notes", "—")),
    ]
    for label, value in fields:
        st.markdown(f'<div class="field-label">{label}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="field-value">{value}</div>', unsafe_allow_html=True)


# ─── sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ContextLink")
    st.caption("Human-in-the-Loop Entity Matching")
    st.divider()

    st.markdown("#### Filters")
    selected_tiers = st.multiselect(
        "Confidence tier",
        options=["HIGH", "MEDIUM", "LOW", "UNCERTAIN"],
        default=["HIGH", "MEDIUM", "LOW", "UNCERTAIN"],
    )
    min_conf = st.slider(
        "Minimum confidence score",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        format="%.2f",
    )

    st.divider()

    filtered = store.filtered_candidates(selected_tiers, min_conf)
    s        = store.stats(filtered)

    st.markdown("#### Session Stats")

    c1, c2 = st.columns(2)
    c1.metric("Entries",        len(df))
    c2.metric("All pairs",      s["total_candidates"])
    c1.metric("Filtered pairs", s["filtered"])
    c2.metric("Reviewed",       s["reviewed"])

    pct = s["reviewed"] / s["filtered"] if s["filtered"] > 0 else 0.0
    st.progress(pct, text=f"{s['reviewed']} / {s['filtered']} reviewed")

    # Tier breakdown — helps researchers see how many pairs fall into each priority band.
    tier_counts = {
        t: sum(1 for c in filtered if c["tier"] == t)
        for t in ("HIGH", "MEDIUM", "LOW", "UNCERTAIN")
    }
    st.markdown(
        " &nbsp;·&nbsp; ".join(
            f"**{t}** {tier_counts[t]}" for t in ("HIGH", "MEDIUM", "LOW", "UNCERTAIN")
        )
    )

    st.divider()

    if st.button("Reset all decisions", use_container_width=True, type="secondary"):
        store.clear()
        st.session_state._selected_decision.clear()
        st.session_state.reviewer_note = ""
        st.rerun()


# ─── main header ──────────────────────────────────────────────────────────────

st.title("ContextLink: Human-in-the-Loop Entity Matching for Research Data")

st.markdown(
    "This tool helps researchers identify possible duplicate people in social network "
    "survey data. Each candidate pair is scored using **name similarity**, **contextual "
    "signals** (location, tie type, relationship, notes), and a combined **confidence score**. "
    "Tier badges (HIGH / MEDIUM / LOW / UNCERTAIN) indicate priority — "
    "but **every decision is yours**. The system only suggests."
)

st.divider()

# ─── review panel ─────────────────────────────────────────────────────────────

current = store.next_unreviewed(filtered)

if not selected_tiers:
    st.warning("Select at least one confidence tier in the sidebar to begin reviewing.")

elif not filtered:
    st.info("No candidate pairs match the current filter settings. Try adjusting the sidebar filters.")

elif current is None:
    st.success(
        f"All {s['filtered']} filtered pairs have been reviewed. "
        "Expand the **Reviewed Decisions** section below to export your results."
    )

else:
    remaining_after = s["filtered"] - s["reviewed"] - 1
    st.markdown(
        f"Reviewing pair **{s['reviewed'] + 1}** of **{s['filtered']}** "
        f"&nbsp;|&nbsp; {remaining_after} remaining after this"
    )

    # ── entry comparison cards ─────────────────────────────────────────────────
    entry_a = lookup_entry(current["id_a"])
    entry_b = lookup_entry(current["id_b"])

    col_a, col_arrow, col_b = st.columns([10, 1, 10])

    with col_a:
        with st.container(border=True):
            render_entry_card(entry_a, "Entry A")

    with col_arrow:
        st.markdown(
            "<div style='display:flex;align-items:center;justify-content:center;"
            "height:100%;padding-top:80px;font-size:1.6rem;color:#adb5bd'>↔</div>",
            unsafe_allow_html=True,
        )

    with col_b:
        with st.container(border=True):
            render_entry_card(entry_b, "Entry B")

    st.divider()

    # ── match signals ──────────────────────────────────────────────────────────
    st.markdown("**Match Signals**")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Confidence Score",    f"{current['confidence']:.3f}")
    m2.metric("Name Similarity",     f"{current['name_score']:.3f}")
    m3.metric("Context Similarity",  f"{current['ctx_score']:.3f}")
    with m4:
        st.markdown("**Tier**")
        st.markdown(tier_badge(current["tier"]), unsafe_allow_html=True)

    # ── signal breakdown ───────────────────────────────────────────────────────
    with st.expander("Signal breakdown", expanded=True):
        name_signals   = [r for r in current["reasons"] if r.startswith("NAME")]
        ctx_signals    = [r for r in current["reasons"] if r.startswith("CONTEXT")]
        safety_signals = [r for r in current["reasons"] if r.startswith("SAFETY")]

        if name_signals:
            st.markdown("**Name signals**")
            for r in name_signals:
                st.markdown(f'<div class="reason-signal">&#x25B8;&nbsp; {r}</div>', unsafe_allow_html=True)

        if ctx_signals:
            st.markdown("**Context signals**")
            for r in ctx_signals:
                st.markdown(f'<div class="reason-signal">&#x25B8;&nbsp; {r}</div>', unsafe_allow_html=True)

        if safety_signals:
            st.markdown("**Safety flags**")
            for r in safety_signals:
                st.warning(r)

    st.divider()

    # ── reviewer decision ──────────────────────────────────────────────────────
    st.markdown("**Your Decision**")

    # Per-tier rationale: tells the reviewer what this tier means for their decision.
    # Uses st.info for HIGH/UNCERTAIN (neutral) and st.warning for MEDIUM/LOW (caution).
    _rationale = TIER_RATIONALE.get(current["tier"], "")
    if _rationale:
        if current["tier"] in ("HIGH", "UNCERTAIN"):
            st.info(_rationale, icon=None)
        else:
            st.warning(_rationale, icon=None)

    # Clear the note from the previous decision before the widget is created.
    # This is the only safe moment: the text_area has not been instantiated yet,
    # so Streamlit does not own reviewer_note and we can write to it freely.
    if st.session_state.pop("_clear_note", False):
        st.session_state.reviewer_note = ""

    st.text_area(
        "Reviewer note (optional)",
        key="reviewer_note",
        placeholder="Add a note explaining your decision — e.g., 'same building, confirmed by location'",
        height=80,
    )

    # Which decision (if any) was selected for this specific candidate pair.
    # None means no decision yet → all buttons render as secondary (no highlight).
    _pair_key = (current["id_a"], current["id_b"])
    _selected = st.session_state._selected_decision.get(_pair_key)

    btn1, btn2, btn3, _ = st.columns([2, 2, 2, 4])
    with btn1:
        if st.button(
            "Approve",
            type="primary" if _selected == "APPROVED" else "secondary",
            use_container_width=True,
            help="These entries refer to the same person",
        ):
            record_decision(current, "APPROVED")
    with btn2:
        if st.button(
            "Reject",
            type="primary" if _selected == "REJECTED" else "secondary",
            use_container_width=True,
            help="These entries refer to different people",
        ):
            record_decision(current, "REJECTED")
    with btn3:
        if st.button(
            "Needs Review",
            type="primary" if _selected == "NEEDS_REVIEW" else "secondary",
            use_container_width=True,
            help="Ambiguous — flag for further investigation",
        ):
            record_decision(current, "NEEDS_REVIEW")


# ─── reviewed decisions table ─────────────────────────────────────────────────

st.divider()
decisions_df = store.decisions_df()
n_reviewed   = len(decisions_df)

with st.expander(
    f"Reviewed Decisions ({n_reviewed} total)",
    expanded=(current is None and n_reviewed > 0),
):
    if decisions_df.empty:
        st.info("No decisions recorded yet. Use the review panel above to get started.")
    else:
        def _highlight_decision(series: pd.Series) -> list[str]:
            styles = []
            for val in series:
                tc, bg = DECISION_COLORS.get(val, ("#383d41", "#e2e3e5"))
                styles.append(f"background-color:{bg};color:{tc};font-weight:600")
            return styles

        styled = decisions_df.style.apply(_highlight_decision, subset=["decision"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        st.download_button(
            label="Download decisions as CSV",
            data=store.to_csv(),
            file_name="contextlink_decisions.csv",
            mime="text/csv",
            use_container_width=True,
        )
