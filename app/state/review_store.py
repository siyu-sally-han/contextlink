"""
state/review_store.py — Review decision store for ContextLink.
Persists human decisions in st.session_state; never writes to disk automatically.
"""

from __future__ import annotations

import pandas as pd
from typing import Optional


class ReviewStore:
    """
    Tracks Approve / Reject / Needs Review decisions for candidate pairs.
    All state lives in memory (via st.session_state); call to_csv() to export.
    """

    def __init__(self, candidates: list[dict]) -> None:
        self.candidates = candidates          # sorted by confidence desc, immutable after init
        self._decisions: dict[tuple[str, str], dict] = {}

    # ── decision management ───────────────────────────────────────────────────

    def record(self, id_a: str, id_b: str, decision: str, note: str = "") -> None:
        self._decisions[(id_a, id_b)] = {
            "id_a":     id_a,
            "id_b":     id_b,
            "decision": decision,
            "note":     note.strip(),
        }

    def is_reviewed(self, id_a: str, id_b: str) -> bool:
        return (id_a, id_b) in self._decisions

    def clear(self) -> None:
        self._decisions.clear()

    # ── queue management ──────────────────────────────────────────────────────

    def filtered_candidates(self, tiers: list[str], min_conf: float) -> list[dict]:
        return [
            c for c in self.candidates
            if c["tier"] in tiers and c["confidence"] >= min_conf
        ]

    def next_unreviewed(self, filtered: list[dict]) -> Optional[dict]:
        return next(
            (c for c in filtered if not self.is_reviewed(c["id_a"], c["id_b"])),
            None,
        )

    # ── stats ─────────────────────────────────────────────────────────────────

    def stats(self, filtered: list[dict]) -> dict:
        reviewed = sum(
            1 for c in filtered if self.is_reviewed(c["id_a"], c["id_b"])
        )
        return {
            "total_candidates": len(self.candidates),
            "filtered":         len(filtered),
            "reviewed":         reviewed,
            "unreviewed":       len(filtered) - reviewed,
        }

    # ── export ────────────────────────────────────────────────────────────────

    def decisions_df(self) -> pd.DataFrame:
        empty_cols = [
            "id_a", "id_b", "name_a", "name_b",
            "confidence", "tier", "decision", "reviewer_note",
        ]
        if not self._decisions:
            return pd.DataFrame(columns=empty_cols)

        rows = []
        for c in self.candidates:
            key = (c["id_a"], c["id_b"])
            if key in self._decisions:
                d = self._decisions[key]
                rows.append({
                    "id_a":          c["id_a"],
                    "id_b":          c["id_b"],
                    "name_a":        c["name_a"],
                    "name_b":        c["name_b"],
                    "confidence":    c["confidence"],
                    "tier":          c["tier"],
                    "decision":      d["decision"],
                    "reviewer_note": d["note"],
                })
        return pd.DataFrame(rows)

    def to_csv(self) -> str:
        return self.decisions_df().to_csv(index=False)
