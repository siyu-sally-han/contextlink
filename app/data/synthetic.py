"""
Synthetic social network survey data generator for ContextLink.
All names, relationships, and locations are entirely fictitious.
No real or private research data is used anywhere in this file.

Intended match clusters and false-positive risks are documented at the bottom.
"""

import pandas as pd
import random

ENTRIES = [
    # ── CLUSTER A ── "Mom / Mama / Mother"
    # Three respondents each refer to the same maternal figure differently.
    # Intended match: A1 ↔ A2 ↔ A3
    {
        "entry_id": "A1", "respondent_id": "R01",
        "alter_name": "Mom", "relationship_label": "mother",
        "tie_type": "strong_tie", "location": "Los Angeles, CA",
        "notes": "calls every Sunday",
    },
    {
        "entry_id": "A2", "respondent_id": "R02",
        "alter_name": "Mama", "relationship_label": "parent",
        "tie_type": "strong_tie", "location": "Los Angeles, CA",
        "notes": "lives nearby, sees her weekly",
    },
    {
        "entry_id": "A3", "respondent_id": "R03",
        "alter_name": "Mother", "relationship_label": "family",
        "tie_type": "strong_tie", "location": "LA",
        "notes": "retired, homemaker",
    },

    # ── CLUSTER B ── "Alex Chen / A. Chen / Alex"
    # Intended match: B1 ↔ B2 ↔ B3
    # False-positive risk: B4 is a different Alex Chen in a different city.
    {
        "entry_id": "B1", "respondent_id": "R04",
        "alter_name": "Alex Chen", "relationship_label": "classmate",
        "tie_type": "weak_tie", "location": "Berkeley, CA",
        "notes": "met in stats class",
    },
    {
        "entry_id": "B2", "respondent_id": "R05",
        "alter_name": "A. Chen", "relationship_label": "study partner",
        "tie_type": "weak_tie", "location": "Berkeley, CA",
        "notes": "works at the library on Tuesdays",
    },
    {
        "entry_id": "B3", "respondent_id": "R06",
        "alter_name": "Alex", "relationship_label": "friend",
        "tie_type": "weak_tie", "location": "Berkeley, CA",
        "notes": "goes by Alex, takes sociology",
    },
    {
        "entry_id": "B4", "respondent_id": "R07",
        "alter_name": "Alex Chen", "relationship_label": "coworker",
        "tie_type": "weak_tie", "location": "San Francisco, CA",
        "notes": "works in tech, met at a conference",
    },

    # ── CLUSTER C ── "B / Brandon"
    # Intended match: C1 ↔ C2
    # False-positive risk: C3 is a different Brandon with a different tie type.
    {
        "entry_id": "C1", "respondent_id": "R08",
        "alter_name": "B", "relationship_label": "roommate",
        "tie_type": "strong_tie", "location": "Seattle, WA",
        "notes": "shares apartment, initial only",
    },
    {
        "entry_id": "C2", "respondent_id": "R09",
        "alter_name": "Brandon", "relationship_label": "roommate",
        "tie_type": "strong_tie", "location": "Seattle, WA",
        "notes": "same building, very close",
    },
    {
        "entry_id": "C3", "respondent_id": "R10",
        "alter_name": "Brandon Lee", "relationship_label": "acquaintance",
        "tie_type": "local_tie", "location": "Portland, OR",
        "notes": "knows from neighborhood events",
    },

    # ── CLUSTER D ── "LR / Lily Ren"
    # Intended match: D1 ↔ D2 ↔ D3
    {
        "entry_id": "D1", "respondent_id": "R11",
        "alter_name": "LR", "relationship_label": "colleague",
        "tie_type": "weak_tie", "location": "Chicago, IL",
        "notes": "initials only, sits across the office",
    },
    {
        "entry_id": "D2", "respondent_id": "R12",
        "alter_name": "Lily Ren", "relationship_label": "coworker",
        "tie_type": "weak_tie", "location": "Chicago, IL",
        "notes": "joined team last spring",
    },
    {
        "entry_id": "D3", "respondent_id": "R13",
        "alter_name": "Lily R.", "relationship_label": "colleague",
        "tie_type": "weak_tie", "location": "Chicago, IL",
        "notes": "from the analytics department",
    },

    # ── CLUSTER E ── "Uncle Wang / Mr. Wang / Wang"
    # Intended match: E1 ↔ E2 ↔ E3
    # False-positive risk: E4 is a different Wang in a different city.
    {
        "entry_id": "E1", "respondent_id": "R14",
        "alter_name": "Uncle Wang", "relationship_label": "uncle",
        "tie_type": "strong_tie", "location": "Houston, TX",
        "notes": "father's brother, visits for holidays",
    },
    {
        "entry_id": "E2", "respondent_id": "R15",
        "alter_name": "Mr. Wang", "relationship_label": "family friend",
        "tie_type": "strong_tie", "location": "Houston, TX",
        "notes": "family calls him Mr. Wang out of respect",
    },
    {
        "entry_id": "E3", "respondent_id": "R16",
        "alter_name": "Wang", "relationship_label": "relative",
        "tie_type": "strong_tie", "location": "Houston, TX",
        "notes": "just calls him Wang",
    },
    {
        "entry_id": "E4", "respondent_id": "R17",
        "alter_name": "David Wang", "relationship_label": "neighbor",
        "tie_type": "local_tie", "location": "Austin, TX",
        "notes": "met at block party, different family",
    },

    # ── CLUSTER F ── "similar relationship labels" edge case
    # F1–F3 all refer to the same person "Jamie" across respondents
    # with varying relationship descriptions.
    # Intended match: F1 ↔ F2 ↔ F3
    {
        "entry_id": "F1", "respondent_id": "R18",
        "alter_name": "Jamie", "relationship_label": "close friend",
        "tie_type": "strong_tie", "location": "New York, NY",
        "notes": "known since undergrad",
    },
    {
        "entry_id": "F2", "respondent_id": "R19",
        "alter_name": "Jamie", "relationship_label": "friend",
        "tie_type": "strong_tie", "location": "New York, NY",
        "notes": "very close, talks daily",
    },
    {
        "entry_id": "F3", "respondent_id": "R20",
        "alter_name": "Jamie K.", "relationship_label": "classmate",
        "tie_type": "weak_tie", "location": "New York, NY",
        "notes": "same program, became close",
    },

    # ── CLUSTER G ── spelling variation "Sara / Sarah"
    # Intended match: G1 ↔ G2
    # False-positive risk: G3 is a different Sarah in a different location.
    {
        "entry_id": "G1", "respondent_id": "R21",
        "alter_name": "Sara Johnson", "relationship_label": "neighbor",
        "tie_type": "local_tie", "location": "Denver, CO",
        "notes": "lives next door, borrows sugar",
    },
    {
        "entry_id": "G2", "respondent_id": "R22",
        "alter_name": "Sarah Johnson", "relationship_label": "neighbor",
        "tie_type": "local_tie", "location": "Denver, CO",
        "notes": "same street, walks dog in the morning",
    },
    {
        "entry_id": "G3", "respondent_id": "R23",
        "alter_name": "Sarah Johnson", "relationship_label": "manager",
        "tie_type": "weak_tie", "location": "Phoenix, AZ",
        "notes": "common name, different person entirely",
    },

    # ── CLUSTER H ── nickname "Mike / Michael / Mikey"
    # Intended match: H1 ↔ H2 ↔ H3
    {
        "entry_id": "H1", "respondent_id": "R24",
        "alter_name": "Mike", "relationship_label": "friend",
        "tie_type": "strong_tie", "location": "Boston, MA",
        "notes": "goes by Mike",
    },
    {
        "entry_id": "H2", "respondent_id": "R25",
        "alter_name": "Michael", "relationship_label": "close friend",
        "tie_type": "strong_tie", "location": "Boston, MA",
        "notes": "full name is Michael, formal contexts",
    },
    {
        "entry_id": "H3", "respondent_id": "R26",
        "alter_name": "Mikey", "relationship_label": "buddy",
        "tie_type": "strong_tie", "location": "Boston, MA",
        "notes": "childhood nickname, still uses it",
    },

    # ── CLUSTER I ── same name, genuinely different people
    # These should NOT be matched — both are named "Chris Park" in different cities.
    # Intended non-match (risky false positive): I1 ≠ I2
    {
        "entry_id": "I1", "respondent_id": "R27",
        "alter_name": "Chris Park", "relationship_label": "coworker",
        "tie_type": "weak_tie", "location": "Miami, FL",
        "notes": "works in marketing, met at onboarding",
    },
    {
        "entry_id": "I2", "respondent_id": "R28",
        "alter_name": "Chris Park", "relationship_label": "gym buddy",
        "tie_type": "local_tie", "location": "Atlanta, GA",
        "notes": "different person, different city, same name",
    },

    # ── CLUSTER J ── partial name / title "Dr. Lee / Prof. Lee / Lee"
    # Intended match: J1 ↔ J2 ↔ J3
    {
        "entry_id": "J1", "respondent_id": "R29",
        "alter_name": "Dr. Lee", "relationship_label": "advisor",
        "tie_type": "weak_tie", "location": "Ann Arbor, MI",
        "notes": "PhD advisor, very supportive",
    },
    {
        "entry_id": "J2", "respondent_id": "R30",
        "alter_name": "Prof. Lee", "relationship_label": "mentor",
        "tie_type": "weak_tie", "location": "Ann Arbor, MI",
        "notes": "same person, known as Prof Lee in class",
    },
    {
        "entry_id": "J3", "respondent_id": "R31",
        "alter_name": "Lee", "relationship_label": "professor",
        "tie_type": "weak_tie", "location": "Ann Arbor, MI",
        "notes": "just calls them Lee informally",
    },

    # ── EXTRA entries to reach 40 total ──
    # Standalone entries — no intended cluster match.
    {
        "entry_id": "X1", "respondent_id": "R32",
        "alter_name": "Grandma Rose", "relationship_label": "grandmother",
        "tie_type": "strong_tie", "location": "Philadelphia, PA",
        "notes": "bakes every weekend",
    },
    {
        "entry_id": "X2", "respondent_id": "R33",
        "alter_name": "Tony Nguyen", "relationship_label": "friend",
        "tie_type": "strong_tie", "location": "San Jose, CA",
        "notes": "met playing basketball",
    },
    {
        "entry_id": "X3", "respondent_id": "R34",
        "alter_name": "Priya M.", "relationship_label": "colleague",
        "tie_type": "weak_tie", "location": "Austin, TX",
        "notes": "works on the same floor",
    },
    {
        "entry_id": "X4", "respondent_id": "R35",
        "alter_name": "Coach Davis", "relationship_label": "coach",
        "tie_type": "local_tie", "location": "Columbus, OH",
        "notes": "youth soccer coach",
    },
    {
        "entry_id": "X5", "respondent_id": "R36",
        "alter_name": "Nana", "relationship_label": "grandmother",
        "tie_type": "strong_tie", "location": "New Orleans, LA",
        "notes": "maternal grandmother, lives alone",
    },
    {
        "entry_id": "X6", "respondent_id": "R37",
        "alter_name": "James T.", "relationship_label": "acquaintance",
        "tie_type": "local_tie", "location": "Nashville, TN",
        "notes": "met at a community event",
    },
    {
        "entry_id": "X7", "respondent_id": "R38",
        "alter_name": "Mei-Ling", "relationship_label": "close friend",
        "tie_type": "strong_tie", "location": "Portland, OR",
        "notes": "childhood friend, still in touch",
    },
    {
        "entry_id": "X8", "respondent_id": "R39",
        "alter_name": "Old Joe", "relationship_label": "neighbor",
        "tie_type": "local_tie", "location": "Detroit, MI",
        "notes": "elderly neighbor, helps with groceries",
    },
    {
        "entry_id": "X9", "respondent_id": "R40",
        "alter_name": "Samantha W.", "relationship_label": "classmate",
        "tie_type": "weak_tie", "location": "Minneapolis, MN",
        "notes": "in the same seminar",
    },
]


def load_entries() -> pd.DataFrame:
    """Return the full synthetic dataset as a DataFrame."""
    random.shuffle(ENTRIES)
    return pd.DataFrame(ENTRIES)


def preview(n: int = 10) -> None:
    """Print a preview of the dataset."""
    df = pd.DataFrame(ENTRIES)  # unshuffled for readability
    print(f"\nTotal entries: {len(df)}\n")
    print(df.head(n).to_string(index=False))
    print("\n--- Intended match clusters ---")
    cluster_notes = [
        "A (A1-A2-A3):  Mom / Mama / Mother           → INTENDED MATCH",
        "B (B1-B2-B3):  Alex Chen / A. Chen / Alex    → INTENDED MATCH   | B4 = different Alex Chen (RISKY FALSE POSITIVE)",
        "C (C1-C2):     B / Brandon                   → INTENDED MATCH   | C3 = Brandon Lee, different city (RISKY FALSE POSITIVE)",
        "D (D1-D2-D3):  LR / Lily Ren / Lily R.       → INTENDED MATCH",
        "E (E1-E2-E3):  Uncle Wang / Mr. Wang / Wang  → INTENDED MATCH   | E4 = David Wang, different city (RISKY FALSE POSITIVE)",
        "F (F1-F2-F3):  Jamie / Jamie K.              → INTENDED MATCH   (relationship labels vary: close friend / friend / classmate)",
        "G (G1-G2):     Sara / Sarah Johnson          → INTENDED MATCH   | G3 = different Sarah Johnson (RISKY FALSE POSITIVE)",
        "H (H1-H2-H3):  Mike / Michael / Mikey        → INTENDED MATCH",
        "I (I1 ≠ I2):   Chris Park × 2               → SHOULD NOT MATCH  (same name, different cities — hardest false positive)",
        "J (J1-J2-J3):  Dr. Lee / Prof. Lee / Lee     → INTENDED MATCH",
        "X (X1-X9):     Standalone entries            → NO INTENDED MATCH",
    ]
    for note in cluster_notes:
        print(" ", note)


if __name__ == "__main__":
    preview()
