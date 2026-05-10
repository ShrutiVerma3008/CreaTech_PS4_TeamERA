"""
scratch/verify_fix1_1.py
========================
Verification script for Fix 1.1 — MAD Override Flag.

Tests:
  1. Overridden outlier floor does NOT appear in identify_unstable_floors()
  2. Non-overridden outlier floor DOES appear
  3. File with no floor_override column still works (backward compatibility)
  4. File with all floor_override=False still works (no regression)

Academic basis verified:
  Leys et al. (2013) J.Exp.Social Psych. 49(4): MAD cannot distinguish
    intentional from unintentional deviation.
  Montgomery (2019) Ch.6: operator override for known special causes.

Exit code 0 + "All assertions pass" on success.
"""
import sys
import os
import pandas as pd
import numpy as np

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from freeze_guard import identify_unstable_floors
from utils.data_loader import validate_and_map

SEP = "=" * 60

# ── Helper: build a minimal valid 10-floor dataframe ──────────────────────
def make_df(n=10, with_override_col=True, outlier_idx=8, override_outlier=True):
    """
    Build a 10-floor DataFrame.
    Floors 0..7 have typical slab_area ~850.
    Floor 8 (outlier_idx): slab_area = 2500 (obvious outlier, ~3× median).
    Floor 9: wall_length = 500 (obvious outlier in that feature).

    override_outlier=True  -> floor 8 gets floor_override=True
    override_outlier=False -> floor 8 gets floor_override=False
    """
    np.random.seed(42)
    n_typical = n - 2  # floors 0..7
    data = {
        "floor_id":      [f"F{i+1:02d}" for i in range(n)],
        "week_start":    list(range(1, n + 1)),
        "week_end":      list(range(2, n + 2)),
        "strip_week":    list(range(4, n + 4)),
        "slab_area_m2":  list(np.random.uniform(840, 860, n_typical)) + [2500.0, 850.0],
        "wall_length_m": list(np.random.uniform(120, 130, n_typical)) + [125.0, 500.0],
        "col_count":     [18] * n,
        "panel_type":    ["ALU-600"] * n,
    }
    df = pd.DataFrame(data)
    # Ensure col_count is int64
    df["col_count"] = df["col_count"].astype(int)

    if with_override_col:
        df["floor_override"] = False
        if override_outlier:
            df.loc[df["floor_id"] == f"F{outlier_idx+1:02d}", "floor_override"] = True
    return df


# ══════════════════════════════════════════════════════════════════
# Test 1 — overridden outlier floor does NOT appear in results
# ══════════════════════════════════════════════════════════════════
print(SEP)
print("TEST 1: Overridden outlier EXCLUDED from unstable list")
print(SEP)
col_map_base = {
    "floor_id":      "floor_id",
    "week_start":    "week_start",
    "week_end":      "week_end",
    "strip_week":    "strip_week",
    "slab_area_m2":  "slab_area_m2",
    "wall_length_m": "wall_length_m",
    "col_count":     "col_count",
    "panel_type":    "panel_type",
    "floor_override":"floor_override",
}

df_with_override = make_df(with_override_col=True, override_outlier=True)
df_validated, auto_cols = validate_and_map(df_with_override, col_map_base)
unstable = identify_unstable_floors(df_validated)

# F09 (index 8) was overridden — must not appear
overridden_floor_id = "F09"
unstable_ids = {u["floor_id"] for u in unstable}
assert overridden_floor_id not in unstable_ids, (
    f"FAIL Test 1: {overridden_floor_id} (overridden) appeared in unstable list: {unstable_ids}"
)
print(f"PASS: '{overridden_floor_id}' (overridden slab outlier) NOT in unstable list")
print(f"      Detected unstable floors: {unstable_ids}")


# ══════════════════════════════════════════════════════════════════
# Test 2 — non-overridden outlier DOES appear
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 2: Non-overridden outlier INCLUDED in unstable list")
print(SEP)

df_no_override = make_df(with_override_col=True, override_outlier=False)
df_validated2, _ = validate_and_map(df_no_override, col_map_base)
unstable2 = identify_unstable_floors(df_validated2)

unstable_ids2 = {u["floor_id"] for u in unstable2}
assert "F09" in unstable_ids2, (
    f"FAIL Test 2: F09 (not overridden, slab=2500) should be unstable. "
    f"Got: {unstable_ids2}"
)
print(f"PASS: 'F09' (non-overridden slab outlier) IS in unstable list")
print(f"      Detected: {unstable_ids2}")


# ══════════════════════════════════════════════════════════════════
# Test 3 — file with NO floor_override column works as before
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 3: No floor_override column — backward compatibility")
print(SEP)

col_map_no_override = {k: v for k, v in col_map_base.items() if k != "floor_override"}
df_no_col = make_df(with_override_col=False)
df_validated3, auto3 = validate_and_map(df_no_col, col_map_no_override)

# validate_and_map must have added floor_override=False for all rows
assert "floor_override" in df_validated3.columns, (
    "FAIL Test 3: floor_override column missing after validate_and_map"
)
assert df_validated3["floor_override"].sum() == 0, (
    "FAIL Test 3: floor_override should be all-False for file with no column"
)

unstable3 = identify_unstable_floors(df_validated3)
unstable_ids3 = {u["floor_id"] for u in unstable3}
assert "F09" in unstable_ids3, (
    f"FAIL Test 3: F09 should still be detected (no overrides). Got: {unstable_ids3}"
)
print(f"PASS: No floor_override column handled correctly (defaults to False)")
print(f"      Detected: {unstable_ids3}")


# ══════════════════════════════════════════════════════════════════
# Test 4 — all floor_override=False is identical to no-column case
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 4: All floor_override=False — no regression vs no-column case")
print(SEP)

df_all_false = make_df(with_override_col=True, override_outlier=False)
df_validated4, _ = validate_and_map(df_all_false, col_map_base)
unstable4 = identify_unstable_floors(df_validated4)
unstable_ids4 = {u["floor_id"] for u in unstable4}

assert unstable_ids4 == unstable_ids3, (
    f"FAIL Test 4: all-False result {unstable_ids4} != no-column result {unstable_ids3}"
)
print(f"PASS: all-False result matches no-column result: {unstable_ids4}")


# ══════════════════════════════════════════════════════════════════
# Test 5 — validate_and_map Check G: coerces mixed types
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 5: validate_and_map coerces mixed floor_override types")
print(SEP)

df_mixed = make_df(with_override_col=True, override_outlier=True)
# Simulate what Excel/CSV gives you: mixed object-type column
# (string "True", integer 1, None alongside booleans)
df_mixed["floor_override"] = df_mixed["floor_override"].astype(object)
df_mixed.loc[0, "floor_override"] = "True"   # string (as read from CSV)
df_mixed.loc[1, "floor_override"] = 1         # integer 1 (Excel numeric)
df_mixed.loc[2, "floor_override"] = None      # None -> should become False
df_validated5, _ = validate_and_map(df_mixed, col_map_base)

assert df_validated5["floor_override"].dtype == bool, (
    f"FAIL Test 5: dtype should be bool, got {df_validated5['floor_override'].dtype}"
)
assert df_validated5.loc[2, "floor_override"] == False, (
    "FAIL Test 5: None should coerce to False"
)
print(f"PASS: floor_override dtype={df_validated5['floor_override'].dtype}, "
      f"None coerced to False correctly")


# ══════════════════════════════════════════════════════════════════
# Test 6 — demo file (F36-F40 overridden)
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 6: Demo file demo_tower_40floors.xlsx — F36-F40 overridden")
print(SEP)

import os
DEMO = os.path.join(os.path.dirname(__file__), "..", "data", "demo_tower_40floors.xlsx")
if os.path.exists(DEMO):
    df_demo_raw = pd.read_excel(DEMO, sheet_name=0)
    demo_headers = list(df_demo_raw.columns)
    assert "floor_override" in demo_headers, (
        f"FAIL Test 6: floor_override missing from demo file headers: {demo_headers}"
    )
    n_override_true = int(df_demo_raw["floor_override"].sum())
    assert n_override_true == 5, (
        f"FAIL Test 6: expected 5 True rows, got {n_override_true}"
    )
    # F36-F40 must be True
    overridden = set(df_demo_raw.loc[df_demo_raw["floor_override"] == True, "floor_id"])
    expected = {"F36", "F37", "F38", "F39", "F40"}
    assert overridden == expected, (
        f"FAIL Test 6: wrong floors overridden. Got {overridden}, expected {expected}"
    )
    print(f"PASS: Demo file has floor_override for F36-F40: {sorted(overridden)}")
else:
    print(f"SKIP Test 6: demo file not found at {DEMO}")


# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("All assertions pass")
print(SEP)
sys.exit(0)
