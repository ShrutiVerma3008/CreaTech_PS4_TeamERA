"""
utils/demand_calc.py
FormOptiX — Demand & Reuse Eligibility Calculations

Academic basis for this module:
  ACI Committee 347. (2014). ACI 347R-14: Guide to Formwork for Concrete.
    American Concrete Institute. Section 5.
  Hanna, A.S. (1998). Concrete Formwork Systems. Marcel Dekker. Chapter 4.
  Peurifoy, R.L., & Oberlender, G.D. (2010). Formwork for Concrete Structures
    (4th ed.). McGraw-Hill. Chapter 7.
  IS 456:2000, Clause 11.3, Table 11 — minimum formwork removal periods
    for RCC structures. Bureau of Indian Standards.
"""

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# IS 456:2000 STRIPPING SCHEDULE
# IS 456:2000, Clause 11.3, Table 11 — minimum formwork removal periods
# for RCC structures. Bureau of Indian Standards.
#
# Component           Minimum cure  → weeks (rounded up)
# ──────────────────────────────────────────────────────
# Walls / columns /
#   vertical faces    24–48 h       → 1 week (procurement-safe rounding)
# Slabs (props left)  3 days        → 1 week (same week, but 1 min)
# Slabs (props rem.)  14 days       → 2 weeks after casting
# Cantilever slabs    21 days       → 3 weeks after casting  ← most conservative
# ─────────────────────────────────────────────────────────────────────────────
def compute_is456_strip_weeks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns df with IS 456:2000-compliant per-component strip week columns.

    New columns added
    -----------------
    strip_week_wall       : week_start + 1  (walls/vertical — 1 wk safe)
    strip_week_slab       : week_start + 2  (slab props removed — 14 days)
    strip_week_cantilever : week_start + 3  (cantilever — 21 days)
    strip_week_user       : original strip_week preserved (or 0 if absent)
    effective_strip_week  : max(strip_week_slab, strip_week_user) when user
                            value is non-zero; strip_week_slab otherwise.
                            Ensures IS 456 minimum is never violated.
    is456_violation       : bool — True if strip_week_user > 0 AND
                            strip_week_user < strip_week_slab (user is
                            requesting stripping earlier than IS 456 allows).

    All strip week values are clipped to week_end + 8 as a safety cap.

    Notes
    -----
    - If strip_week column is absent, it is auto-generated as week_end + 2
      (matching the existing sidebar default) before IS 456 logic is applied.
    - IS 456:2000, Clause 11.3, Table 11 — minimum formwork removal periods
      for RCC structures.
    """
    df = df.copy()

    # ── Guard: ensure strip_week column exists ────────────────────────────
    if "strip_week" not in df.columns:
        if "week_end" in df.columns:
            df["strip_week"] = df["week_end"] + 2   # default 2-week buffer
        else:
            df["strip_week"] = 0

    # ── Preserve user value ───────────────────────────────────────────────
    df["strip_week_user"] = df["strip_week"].fillna(0).astype(int)

    # ── IS 456:2000 Cl.11.3 component strip weeks ─────────────────────────
    # IS 456:2000, Clause 11.3, Table 11 — minimum formwork removal periods
    # for RCC structures. Bureau of Indian Standards.
    _cap = (df["week_end"] + 8) if "week_end" in df.columns else df["strip_week_user"] + 8

    df["strip_week_wall"] = (
        (df["week_start"] + 1).clip(upper=_cap)
    )
    df["strip_week_slab"] = (
        (df["week_start"] + 2).clip(upper=_cap)     # 14 days → 2 weeks
    )
    df["strip_week_cantilever"] = (
        (df["week_start"] + 3).clip(upper=_cap)     # 21 days → 3 weeks
    )

    # ── Effective strip week: respect user value but enforce IS 456 minimum ─
    # If user provided a value (> 0), use max(user, IS-456-slab).
    # If user left it blank (0), use IS-456-slab.
    user_valid = df["strip_week_user"] > 0
    df["effective_strip_week"] = np.where(
        user_valid,
        np.maximum(df["strip_week_user"], df["strip_week_slab"]),
        df["strip_week_slab"],
    ).astype(int)

    # ── Violation flag ────────────────────────────────────────────────────
    # True when user explicitly requests stripping BEFORE IS 456 minimum.
    df["is456_violation"] = (
        user_valid & (df["strip_week_user"] < df["strip_week_slab"])
    ).astype(bool)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# REUSE ELIGIBILITY MATRIX
# Based on: Hanna (1998) Ch.4 — panel cycling logistics
# and ACI 347R-14 S.5 — minimum strip time before reuse.
# eligible[i][j] = True means floor i panels can reach
# floor j before floor j construction begins.
#
# CHANGE (IS 456 integration): uses 'effective_strip_week' when present;
# falls back to 'strip_week' for backward-compat with synthetic data.
# ─────────────────────────────────────────────────────────────────────────────
def build_reuse_matrix(df: pd.DataFrame, transport_weeks: int = 1) -> pd.DataFrame:
    """
    Build a boolean reuse-eligibility matrix for a set of floors.

    Parameters
    ----------
    df : pd.DataFrame
        Validated floor dataframe with columns:
        floor_id, week_start, week_end, strip_week
        (and optionally effective_strip_week from compute_is456_strip_weeks)
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
            effective_strip_week[i] + transport_weeks <= week_start[j]
            AND i != j

    Physical meaning
    ----------------
    eligible[i][j] = True  → panels stripped from floor i can
                              physically arrive at floor j before
                              floor j's construction begins.

    IS 456 note
    -----------
    Uses effective_strip_week (IS 456:2000 Cl.11.3 compliant) when present.
    Falls back to strip_week for synthetic-mode data that has not been
    processed by compute_is456_strip_weeks().
    """
    # IS 456:2000, Clause 11.3, Table 11 — minimum formwork removal periods
    # for RCC structures. Use IS-456-compliant strip week when available.
    strip_col = (
        "effective_strip_week" if "effective_strip_week" in df.columns
        else "strip_week"
    )

    floor_ids   = df["floor_id"].tolist()
    strip_weeks = df.set_index("floor_id")[strip_col]
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


# ──────────────────────────────────────────────────────────────────────────────
# Standalone test
# ──────────────────────────────────────────────────────────────────────────────
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

    # ── Test compute_is456_strip_weeks ─────────────────────────────────────
    print("=" * 60)
    print("compute_is456_strip_weeks() -- IS 456:2000 Cl.11.3 test")
    print("=" * 60)
    df_456 = compute_is456_strip_weeks(test_df)
    print(df_456[[
        "floor_id", "week_start", "strip_week_wall", "strip_week_slab",
        "strip_week_cantilever", "strip_week_user", "effective_strip_week",
        "is456_violation"
    ]].to_string(index=False))

    # All effective_strip_week should equal week_start + 2 (slab, no cantilevers)
    # since user strip_week > strip_week_slab for all rows in this test.
    for _, row in df_456.iterrows():
        esw = row["effective_strip_week"]
        sw_slab = row["strip_week_slab"]
        user = row["strip_week_user"]
        expected = max(user, sw_slab) if user > 0 else sw_slab
        assert esw == expected, f"Floor {row['floor_id']}: expected {expected}, got {esw}"
    print("PASS: IS 456 column test passed.")
    print()

    # ── Test build_reuse_matrix with IS 456 columns ───────────────────────
    matrix = build_reuse_matrix(df_456, transport_weeks=1)

    print("=" * 60)
    print("build_reuse_matrix() -- using effective_strip_week")
    print("transport_weeks = 1")
    print("=" * 60)
    print(matrix.to_string())
    print()

    true_count  = matrix.values.sum()
    false_count = (~matrix.values).sum() - len(matrix)  # subtract diagonal
    print(f"True cells  (excl. diagonal): {true_count}")
    print(f"False cells (excl. diagonal): {false_count}")
    assert true_count  > 0, "Expected at least one True cell"
    assert false_count > 0, "Expected at least one False cell"
    print("PASS: Reuse matrix test passed.")
