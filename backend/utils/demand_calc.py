"""
utils/demand_calc.py
FormOptiX — Demand & Reuse Eligibility Calculations

Academic basis for this module:
  ACI Committee 347. (2014). ACI 347R-14: Guide to Formwork for Concrete.
    American Concrete Institute. Section 5.
  Hanna, A.S. (1998). Concrete Formwork Systems. Marcel Dekker. Chapter 4.
  Peurifoy, R.L., & Oberlender, G.D. (2010). Formwork for Concrete Structures
    (4th ed.). McGraw-Hill. Chapter 7.
"""

import pandas as pd
import numpy as np


# Reuse eligibility matrix
# Based on: Hanna (1998) Ch.4 — panel cycling logistics
# and ACI 347R-14 S.5 — minimum strip time before reuse.
# eligible[i][j] = True means floor i panels can reach
# floor j before floor j construction begins.
def build_reuse_matrix(df: pd.DataFrame, transport_weeks: int = 1) -> pd.DataFrame:
    """
    Build a boolean reuse-eligibility matrix for a set of floors.

    Parameters
    ----------
    df : pd.DataFrame
        Validated floor dataframe with columns:
        floor_id, week_start, week_end, strip_week
    transport_weeks : int, default 1
        Number of weeks required to move panels between floors after
        stripping. Hanna (1998) Ch.4: typically 1 week for on-site
        vertical movement.

    Returns
    -------
    pd.DataFrame
        Boolean DataFrame of shape (n_floors, n_floors).
        Index and columns are floor_id values.
        eligible[i][j] = True iff:
            strip_week[i] + transport_weeks <= week_start[j]
            AND i != j

    Physical meaning
    ----------------
    eligible[i][j] = True  → panels stripped from floor i can
                              physically arrive at floor j before
                              floor j's construction begins.
    """
    floor_ids = df["floor_id"].tolist()
    strip_weeks = df.set_index("floor_id")["strip_week"]
    week_starts = df.set_index("floor_id")["week_start"]

    eligible = pd.DataFrame(False, index=floor_ids, columns=floor_ids)

    for i in floor_ids:
        for j in floor_ids:
            if i == j:
                continue
            # ACI 347R-14 S.5: panel from i can reach j only after
            # stripping + transport time (Hanna, 1998, Ch.4)
            if strip_weeks[i] + transport_weeks <= week_starts[j]:
                eligible.at[i, j] = True

    return eligible


# ──────────────────────────────────────────────────────────────
# Standalone test
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 4-floor example that produces at least one True and one False cell.
    # Floor A builds first (weeks 1-4, strips week 6).
    # Floor B builds next (weeks 3-6, strips week 8).
    # Floor C builds late (weeks 9-12, strips week 14).
    # Floor D builds very late (weeks 15-18, strips week 20).
    test_df = pd.DataFrame([
        {"floor_id": "A", "week_start": 1,  "week_end": 4,  "strip_week": 6},
        {"floor_id": "B", "week_start": 3,  "week_end": 6,  "strip_week": 8},
        {"floor_id": "C", "week_start": 9,  "week_end": 12, "strip_week": 14},
        {"floor_id": "D", "week_start": 15, "week_end": 18, "strip_week": 20},
    ])

    matrix = build_reuse_matrix(test_df, transport_weeks=1)

    print("=" * 50)
    print("build_reuse_matrix() -- 4-floor standalone test")
    print("transport_weeks = 1")
    print("=" * 50)
    print(matrix.to_string())
    print()
    print("Expected True  cells (at minimum):")
    print("  A -> C : strip_week[A]=6  + 1 <= week_start[C]=9   [OK]")
    print("  A -> D : strip_week[A]=6  + 1 <= week_start[D]=15  [OK]")
    print("  B -> C : strip_week[B]=8  + 1 <= week_start[C]=9   [OK]")
    print("  B -> D : strip_week[B]=8  + 1 <= week_start[D]=15  [OK]")
    print("  C -> D : strip_week[C]=14 + 1 <= week_start[D]=15  [OK]")
    print()
    print("Expected False cells (at minimum):")
    print("  A -> B : strip_week[A]=6  + 1=7  > week_start[B]=3  [FAIL expected]")
    print("  B -> A : strip_week[B]=8  + 1=9  > week_start[A]=1  [FAIL expected]")
    print("  C -> A : strip_week[C]=14 + 1=15 > week_start[A]=1  [FAIL expected]")
    print()
    true_count  = matrix.values.sum()
    false_count = (~matrix.values).sum() - len(matrix)  # subtract diagonal
    print(f"True cells  (excl. diagonal): {true_count}")
    print(f"False cells (excl. diagonal): {false_count}")
    assert true_count  > 0, "Expected at least one True cell"
    assert false_count > 0, "Expected at least one False cell"
    print("PASS: Test passed.")

