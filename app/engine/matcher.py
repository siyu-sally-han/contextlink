"""
engine/matcher.py — ContextLink matching engine.

Generates candidate pairs from synthetic survey entries, scores each pair on
name similarity and context similarity, and assigns a human-readable confidence
tier. No automatic identity decisions are made; all output is for human review.
"""

from __future__ import annotations

import os
import re
import sys
from itertools import combinations
from typing import Optional

import pandas as pd
from rapidfuzz import fuzz

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.synthetic import load_entries


# ─── constants ────────────────────────────────────────────────────────────────

FAMILY_ROLES: dict[str, str] = {
    "mom": "maternal_parent",
    "mama": "maternal_parent",
    "mother": "maternal_parent",
    "mommy": "maternal_parent",
    "ma": "maternal_parent",
    "dad": "paternal_parent",
    "daddy": "paternal_parent",
    "father": "paternal_parent",
    "papa": "paternal_parent",
    "pop": "paternal_parent",
    "grandma": "grandparent",
    "grandmother": "grandparent",
    "nana": "grandparent",
    "granny": "grandparent",
    "grandpa": "grandparent",
    "grandfather": "grandparent",
    "gramps": "grandparent",
}

TITLE_PREFIXES: frozenset[str] = frozenset({
    "dr", "prof", "professor", "mr", "mrs", "ms", "miss",
    "uncle", "aunt", "coach", "sir", "rev", "reverend",
})

NICKNAME_GROUPS: list[frozenset[str]] = [
    frozenset({"mike", "michael", "mikey", "mick", "mickey"}),
    frozenset({"bob", "robert", "rob", "bobby"}),
    frozenset({"bill", "william", "will", "billy", "liam"}),
    frozenset({"jim", "james", "jimmy", "jamie"}),
    frozenset({"alex", "alexander", "xander", "al"}),
    frozenset({"chris", "christopher", "kristopher"}),
    frozenset({"katie", "kate", "katherine", "kathy", "kat"}),
    frozenset({"liz", "elizabeth", "beth", "betty", "ellie"}),
    frozenset({"sam", "samuel", "samantha"}),
    frozenset({"dan", "daniel", "danny"}),
    frozenset({"tom", "thomas", "tommy"}),
    frozenset({"joe", "joseph", "joey"}),
    frozenset({"ben", "benjamin", "benji"}),
    frozenset({"tony", "anthony", "ant"}),
    frozenset({"jen", "jennifer", "jenny"}),
    frozenset({"sue", "susan", "susie"}),
    frozenset({"meg", "megan", "maggie"}),
    frozenset({"nick", "nicholas", "nico"}),
    frozenset({"pat", "patricia", "patrick"}),
    frozenset({"jack", "john", "johnny", "jon"}),
]

REL_GROUPS: dict[str, frozenset[str]] = {
    "family": frozenset({
        "mother", "father", "parent", "family", "relative",
        "uncle", "aunt", "grandmother", "grandfather",
        "sibling", "brother", "sister", "cousin",
    }),
    "friend": frozenset({
        "friend", "close friend", "buddy", "pal", "best friend",
    }),
    "classmate": frozenset({
        "classmate", "study partner", "schoolmate", "lab partner",
    }),
    "colleague": frozenset({
        "colleague", "coworker", "work friend", "work colleague",
    }),
    "neighbor": frozenset({
        "neighbor", "local friend", "neighborhood friend",
    }),
    "acquaintance": frozenset({
        "acquaintance", "casual friend", "loose contact",
    }),
    "mentor": frozenset({
        "advisor", "mentor", "professor", "coach", "supervisor", "manager",
    }),
    "roommate": frozenset({
        "roommate", "housemate", "flatmate",
    }),
}

# Semantic adjacency between relationship groups
REL_ADJACENT: dict[str, frozenset[str]] = {
    "friend":      frozenset({"classmate", "acquaintance", "roommate"}),
    "classmate":   frozenset({"friend", "colleague"}),
    "colleague":   frozenset({"mentor", "classmate"}),
    "mentor":      frozenset({"colleague"}),
    "neighbor":    frozenset({"acquaintance"}),
    "acquaintance": frozenset({"friend", "neighbor"}),
    "roommate":    frozenset({"friend"}),
}

CITY_ALIASES: dict[str, str] = {
    "la":     "los angeles",
    "sf":     "san francisco",
    "nyc":    "new york",
    "ny":     "new york",
    "dc":     "washington",
    "philly": "philadelphia",
}

STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "in", "at", "on", "for",
    "to", "of", "is", "he", "she", "they", "very", "same",
    "has", "have", "from", "with", "as", "by", "his", "her",
})

MIN_NAME_SIM_THRESHOLD = 0.25
NAME_WEIGHT = 0.60
CTX_WEIGHT  = 0.40


# ─── name normalization ────────────────────────────────────────────────────────

def normalize_name(raw: str) -> str:
    """
    Canonical form for comparison:
      1. Lowercase, strip punctuation.
      2. Resolve family-role labels (Mom → maternal_parent).
      3. Strip honorific / relational prefixes (Dr., Uncle, Coach, etc.).
    """
    name = raw.strip().lower()
    name = re.sub(r"[^\w\s]", "", name)   # remove punctuation
    name = re.sub(r"\s+", " ", name).strip()

    if name in FAMILY_ROLES:
        return FAMILY_ROLES[name]

    tokens = [t for t in name.split() if t not in TITLE_PREFIXES]
    return " ".join(tokens) if tokens else name


def _is_single_initial(s: str) -> bool:
    return len(s) == 1 and s.isalpha()


def _is_packed_initials(s: str) -> bool:
    """True for 2–4 uppercase-only chars like 'LR' or 'ABC' (stored lowercase as 'lr', 'abc')."""
    return 2 <= len(s) <= 4 and s.isalpha() and " " not in s


def _initials_match(short: str, long_name: str) -> bool:
    """
    Check whether `short` could be initials for `long_name`.
      'b'  → 'brandon'        : True  (single initial)
      'lr' → 'lily ren'       : True  (multi-initial, L=Lily R=Ren)
      'a'  → 'alex chen'      : True  (matches first token)
    """
    tokens = long_name.split()
    if _is_single_initial(short):
        return any(t.startswith(short) for t in tokens)
    if _is_packed_initials(short) and len(short) == len(tokens):
        return all(tok.startswith(ch) for ch, tok in zip(short, tokens))
    return False


def _nickname_match(n1: str, n2: str) -> bool:
    """True if both first tokens share a nickname group."""
    t1 = n1.split()[0] if n1.split() else n1
    t2 = n2.split()[0] if n2.split() else n2
    return any(t1 in grp and t2 in grp for grp in NICKNAME_GROUPS)


# ─── name similarity ──────────────────────────────────────────────────────────

def name_similarity(raw1: str, raw2: str) -> tuple[float, list[str]]:
    """
    Returns (score 0–1, reason_codes).
    Applies intentional caps for very short / initial-only names so that
    weak name evidence cannot push a pair to HIGH on its own.
    """
    n1 = normalize_name(raw1)
    n2 = normalize_name(raw2)
    reasons: list[str] = []

    # 1. Family-role canonical match
    if n1 == n2 and n1 in set(FAMILY_ROLES.values()):
        reasons.append(f"NAME: family role match ({n1})")
        return 1.0, reasons

    # 2. Exact match after normalization
    if n1 == n2:
        reasons.append(f"NAME: exact match after normalization ({n1!r})")
        return 1.0, reasons

    # 3. Nickname group match (Mike / Michael / Mikey)
    if _nickname_match(n1, n2):
        base = fuzz.token_sort_ratio(n1, n2) / 100
        score = max(base, 0.88)
        reasons.append(f"NAME: nickname group match ({n1!r} ↔ {n2!r})")
        return min(score, 1.0), reasons

    # 4. Initials expansion (one name is short/initial of the other)
    short, long = (n1, n2) if len(n1) <= len(n2) else (n2, n1)
    if _initials_match(short, long):
        if _is_single_initial(short):
            score = 0.65
            reasons.append(
                f"NAME: single-initial expansion ({short!r} → {long!r}); "
                "weak signal — context required"
            )
        else:
            score = 0.72
            reasons.append(f"NAME: multi-initial expansion ({short!r} → {long!r})")
        return score, reasons

    # 5. Token-level prefix / abbreviation match (A. Chen → Alex Chen)
    t1, t2 = n1.split(), n2.split()
    if len(t1) == len(t2) and len(t1) >= 1:
        matches = sum(
            1 for a, b in zip(t1, t2)
            if a == b or b.startswith(a) or a.startswith(b)
        )
        if matches == len(t1):
            base = fuzz.token_sort_ratio(n1, n2) / 100
            score = max(base, 0.78)
            reasons.append(f"NAME: abbreviated token match ({n1!r} ↔ {n2!r})")
            return min(score, 1.0), reasons

    # 6. Fuzzy fallback
    base    = fuzz.token_sort_ratio(n1, n2) / 100
    partial = fuzz.partial_ratio(n1, n2) / 100
    score   = max(base, partial * 0.9)

    label = (
        "high"     if score >= 0.85 else
        "moderate" if score >= 0.60 else
        "low"
    )
    reasons.append(f"NAME: {label} fuzzy similarity {score:.0%} ({n1!r} ↔ {n2!r})")
    return score, reasons


# ─── context similarity ────────────────────────────────────────────────────────

def _normalize_location(loc: str) -> str:
    loc = re.sub(r"[^\w\s,]", "", loc.strip().lower())
    city = loc.split(",")[0].strip()
    return CITY_ALIASES.get(city, city)


def _location_score(l1: str, l2: str) -> tuple[float, list[str]]:
    c1, c2 = _normalize_location(l1), _normalize_location(l2)
    if c1 == c2:
        return 1.0, [f"CONTEXT: same city ({c1})"]
    state1 = l1.strip().split(",")[-1].strip().lower() if "," in l1 else ""
    state2 = l2.strip().split(",")[-1].strip().lower() if "," in l2 else ""
    if state1 and state2 and state1 == state2:
        return 0.30, [f"CONTEXT: same state ({state1})"]
    return 0.0, [f"CONTEXT: different locations ({l1!r} vs {l2!r})"]


def _rel_group(label: str) -> Optional[str]:
    label = label.strip().lower()
    for group, members in REL_GROUPS.items():
        if label in members:
            return group
    return None


def _rel_score(r1: str, r2: str) -> tuple[float, list[str]]:
    g1, g2 = _rel_group(r1), _rel_group(r2)
    if g1 and g2:
        if g1 == g2:
            return 1.0, [f"CONTEXT: same relationship group ({g1})"]
        if g2 in REL_ADJACENT.get(g1, frozenset()):
            return 0.50, [f"CONTEXT: adjacent relationship groups ({g1} ↔ {g2})"]
    raw_sim = fuzz.token_sort_ratio(r1.lower(), r2.lower()) / 100
    if raw_sim >= 0.70:
        return raw_sim * 0.8, [f"CONTEXT: similar relationship labels ({r1!r} ≈ {r2!r})"]
    return 0.0, [f"CONTEXT: different relationship labels ({r1!r} vs {r2!r})"]


def _notes_overlap(n1: str, n2: str) -> tuple[float, list[str]]:
    def keywords(text: str) -> set[str]:
        return {
            w for w in re.findall(r"\w+", text.lower())
            if w not in STOPWORDS and len(w) > 2
        }
    w1, w2 = keywords(n1), keywords(n2)
    if not w1 or not w2:
        return 0.0, []
    shared = w1 & w2
    jaccard = len(shared) / len(w1 | w2)
    if jaccard > 0.12:
        return jaccard, [f"CONTEXT: shared note keywords {sorted(shared)}"]
    return 0.0, []


def context_similarity(e1: dict, e2: dict) -> tuple[float, list[str]]:
    """
    Weighted combination of location, tie_type, relationship group, and notes.
    Returns (score 0–1, reason_codes).
    """
    reasons: list[str] = []

    loc_score, loc_r = _location_score(e1["location"], e2["location"])
    reasons.extend(loc_r)

    if e1["tie_type"] == e2["tie_type"]:
        tie_score = 1.0
        reasons.append(f"CONTEXT: same tie type ({e1['tie_type']})")
    else:
        tie_score = 0.0
        reasons.append(f"CONTEXT: different tie types ({e1['tie_type']} vs {e2['tie_type']})")

    rel_score, rel_r = _rel_score(e1["relationship_label"], e2["relationship_label"])
    reasons.extend(rel_r)

    notes_score, notes_r = _notes_overlap(e1["notes"], e2["notes"])
    reasons.extend(notes_r)

    score = (
        0.35 * loc_score
        + 0.20 * tie_score
        + 0.30 * rel_score
        + 0.15 * notes_score
    )
    return score, reasons


# ─── pair scoring with safety rules ───────────────────────────────────────────

def score_pair(e1: dict, e2: dict) -> dict:
    """
    Score one candidate pair and return a structured result.

    Safety rules applied after combining signals:
      1. Single-character names: confidence capped at MEDIUM (≤ 0.75).
      2. Packed 2-char initials (e.g. 'LR'): confidence capped at MEDIUM (≤ 0.78).
      3. Identical names in different locations: capped at LOW (≤ 0.55) —
         common names across cities are high-risk false positives.
    """
    name_score, name_reasons = name_similarity(e1["alter_name"], e2["alter_name"])
    ctx_score,  ctx_reasons  = context_similarity(e1, e2)

    confidence    = NAME_WEIGHT * name_score + CTX_WEIGHT * ctx_score
    safety_flags: list[str] = []

    n1    = normalize_name(e1["alter_name"])
    n2    = normalize_name(e2["alter_name"])
    short = n1 if len(n1) <= len(n2) else n2

    # Safety 1 — single initial.
    # Flag fires whenever a single-letter name is involved, regardless of whether
    # the score is already below the cap. The cap protects against context pushing
    # it to HIGH; the flag ensures the reviewer always sees the warning.
    if _is_single_initial(short):
        if confidence > 0.75:
            confidence = 0.75
        safety_flags.append(
            "SAFETY: single-initial name — identity cannot be confirmed from one letter alone; "
            "confidence capped at MEDIUM"
        )

    # Safety 2 — packed two-letter initials (e.g. 'LR').
    # Same principle: flag unconditionally, cap only when needed.
    elif _is_packed_initials(short) and len(short) == 2:
        if confidence > 0.78:
            confidence = 0.78
        safety_flags.append(
            f"SAFETY: two-letter initials ({short.upper()!r}) — initials are ambiguous without "
            "corroborating context; confidence capped at MEDIUM"
        )

    # Safety 3 — identical name, different locations
    if n1 == n2 and n1 not in set(FAMILY_ROLES.values()):
        loc1 = _normalize_location(e1["location"])
        loc2 = _normalize_location(e2["location"])
        if loc1 != loc2 and confidence > 0.55:
            confidence = 0.55
            safety_flags.append(
                f"SAFETY: identical name ({n1!r}) across different locations — "
                "high false-positive risk; routed to LOW for mandatory human review"
            )

    tier = _confidence_tier(confidence)
    return {
        "id_a":       e1["entry_id"],
        "id_b":       e2["entry_id"],
        "name_a":     e1["alter_name"],
        "name_b":     e2["alter_name"],
        "name_score": round(name_score, 3),
        "ctx_score":  round(ctx_score,  3),
        "confidence": round(confidence, 3),
        "tier":       tier,
        "reasons":    name_reasons + ctx_reasons + safety_flags,
    }


def _confidence_tier(score: float) -> str:
    if score >= 0.80:
        return "HIGH"
    if score >= 0.60:
        return "MEDIUM"
    if score >= 0.40:
        return "LOW"
    return "UNCERTAIN"


# ─── candidate generation ──────────────────────────────────────────────────────

def generate_candidates(
    df: pd.DataFrame,
    min_name_sim: float = MIN_NAME_SIM_THRESHOLD,
) -> list[dict]:
    """
    Generate scored candidate pairs.
    Blocking: pairs whose name_score falls below min_name_sim are skipped.
    Same-respondent pairs are always skipped.
    Returns candidates sorted by confidence descending.
    """
    records = df.to_dict(orient="records")
    candidates: list[dict] = []

    for e1, e2 in combinations(records, 2):
        if e1["respondent_id"] == e2["respondent_id"]:
            continue
        n_score, _ = name_similarity(e1["alter_name"], e2["alter_name"])
        if n_score < min_name_sim:
            continue
        candidates.append(score_pair(e1, e2))

    candidates.sort(key=lambda x: x["confidence"], reverse=True)
    return candidates


# ─── smoke test ───────────────────────────────────────────────────────────────

def _find_pair(candidates: list[dict], id_a: str, id_b: str) -> Optional[dict]:
    target = {id_a, id_b}
    return next((c for c in candidates if {c["id_a"], c["id_b"]} == target), None)


def _print_result(label: str, result: Optional[dict]) -> None:
    sep = "─" * 70
    if result is None:
        print(f"\n{sep}")
        print(f"  [{label}]  NOT IN CANDIDATES (blocked by name threshold)")
        return
    tier_marker = {"HIGH": "★★★", "MEDIUM": "★★ ", "LOW": "★  ", "UNCERTAIN": "?  "}.get(result["tier"], "   ")
    print(f"\n{sep}")
    print(f"  [{label}]  {tier_marker} {result['tier']}")
    print(f"  Pair    : {result['name_a']!r}  ↔  {result['name_b']!r}  ({result['id_a']} / {result['id_b']})")
    print(f"  Scores  : name={result['name_score']:.3f}  ctx={result['ctx_score']:.3f}  confidence={result['confidence']:.3f}")
    print("  Signals :")
    for r in result["reasons"]:
        print(f"    • {r}")


def smoke_test() -> None:
    df = load_entries()
    candidates = generate_candidates(df)
    print(f"\n{'═'*70}")
    print(f"  CONTEXTLINK SMOKE TEST — {len(candidates)} candidate pairs generated")
    print(f"{'═'*70}")

    tests = [
        ("Mom / Mama  [family role alias]",              "A1", "A2"),
        ("B / Brandon  [single initial]",                "C1", "C2"),
        ("LR / Lily Ren  [multi-initial]",               "D1", "D2"),
        ("Alex Chen / A. Chen  [abbreviation]",          "B1", "B2"),
        ("Chris Park × 2  [same name, diff city]",       "I1", "I2"),
    ]
    for label, id_a, id_b in tests:
        _print_result(label, _find_pair(candidates, id_a, id_b))

    print(f"\n{'─'*70}")
    print("  TOP 15 CANDIDATE PAIRS")
    print(f"{'─'*70}")
    header = f"  {'ID pair':<10} {'Name A':<18} {'Name B':<18} {'conf':>6}  {'tier'}"
    print(header)
    for r in candidates[:15]:
        pair  = f"{r['id_a']}↔{r['id_b']}"
        print(f"  {pair:<10} {r['name_a']:<18} {r['name_b']:<18} {r['confidence']:>6.3f}  {r['tier']}")
    print()


if __name__ == "__main__":
    smoke_test()
