"""
scratch/verify_fix3_0.py
========================
Verification script for Fix 3.0 — IS 456:2000 Stripping Schedule.

Tests:
  1. get_strip_weeks_is456: ALU-600=2, ALU-450=1, H20-beam=2
  2. get_strip_weeks_aci: all rows = 2 (flat)
  3. validate_and_map with IS456 -> strip_week = week_end + IS456 delta
  4. validate_and_map with ACI347R-14 -> strip_week = week_end + 2 for all
  5. User-provided strip_week preserved unchanged under both standards
  6. Unknown SKU defaults to 2 weeks under IS456
  7. panel_type column accepted (not just 'sku')

Academic basis:
  IS 456:2000 Cl.11.3 (BIS): mandatory Indian standard for stripping time.
  ACI 347R-14 S.5 (2014): American standard, flat 2-week buffer.
  Hanna (1998) Ch.4: stripping time controls panel reuse eligibility.

Exit code 0 + "All assertions pass" on success.
"""
import sys
import os
import pandas as pd
import numpy as np

# Bypass streamlit import inside data_loader when running standalone
import unittest.mock as mock
import streamlit as _st_real

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch st.error, st.stop, st.warning so validate_and_map runs headlessly
import streamlit as st
st.error   = lambda msg: None
st.warning = lambda msg: None
st.stop    = lambda: (_ for _ in ()).throw(SystemExit("st.stop called"))
st.info    = lambda msg: None
st.success = lambda msg: None

from utils.data_loader import (
    get_strip_weeks_is456,
    get_strip_weeks_aci,
    validate_and_map,
    SKU_STRIP_WEEKS_IS456,
    DEFAULT_STRIP_WEEKS_IS456,
)

SEP = "=" * 60


# ── Helper: build 6-floor mock DataFrame ─────────────────────────────────────
def make_df(with_strip_week: bool = False) -> pd.DataFrame:
    """
    6-floor mock with 2x ALU-600, 2x ALU-450, 2x H20-beam.
    week_start = i+1, week_end = i+2.
    """
    rows = []
    skus = ["ALU-600", "ALU-600", "ALU-450", "ALU-450", "H20-beam", "H20-beam"]
    for i, sku in enumerate(skus):
        row = {
            "floor_id":       f"F{i+1:02d}",
            "week_start":     i + 1,
            "week_end":       i + 2,
            "slab_area_m2":   100.0 + i * 5,
            "wall_length_m":  30.0 + i,
            "col_count":      8,
            "panel_type":     sku,
        }
        if with_strip_week:
            row["strip_week"] = i + 10   # user-supplied: week_end + 8
        rows.append(row)
    return pd.DataFrame(rows)


def make_col_map(df: pd.DataFrame) -> dict:
    """Identity mapping — all columns already named correctly."""
    required = [
        "floor_id", "week_start", "week_end",
        "slab_area_m2", "wall_length_m", "col_count", "panel_type"
    ]
    return {c: c for c in required if c in df.columns}


# ══════════════════════════════════════════════════════════════════
# Test 1 — get_strip_weeks_is456: correct values per SKU
# ══════════════════════════════════════════════════════════════════
print(SEP)
print("TEST 1: get_strip_weeks_is456 — ALU-600=2, ALU-450=1, H20-beam=2")
print(SEP)

df = make_df()
# Use panel_type column (get_strip_weeks_is456 accepts both sku and panel_type)
df_sku = df.rename(columns={"panel_type": "sku"})
deltas = get_strip_weeks_is456(df_sku)

expected = [2, 2, 1, 1, 2, 2]
for i, (got, exp) in enumerate(zip(deltas.tolist(), expected)):
    sku = df_sku["sku"].iloc[i]
    assert got == exp, f"FAIL Test 1: row {i} SKU={sku}, expected delta={exp}, got {got}"
    print(f"  PASS row {i}: {sku} -> delta={got}")

# Also test with panel_type column directly
deltas_pt = get_strip_weeks_is456(df)  # df has panel_type, not sku
for i, (got, exp) in enumerate(zip(deltas_pt.tolist(), expected)):
    assert got == exp, (
        f"FAIL Test 1 (panel_type): row {i}, expected {exp}, got {got}"
    )
print("PASS: Both 'sku' and 'panel_type' column accepted")


# ══════════════════════════════════════════════════════════════════
# Test 2 — get_strip_weeks_aci: all rows = 2
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 2: get_strip_weeks_aci — all rows = 2 (flat)")
print(SEP)

aci_deltas = get_strip_weeks_aci(df)
assert list(aci_deltas) == [2] * 6, (
    f"FAIL Test 2: expected all 2s, got {list(aci_deltas)}"
)
print(f"PASS: get_strip_weeks_aci returns {list(aci_deltas)}")


# ══════════════════════════════════════════════════════════════════
# Test 3 — validate_and_map IS456: strip_week = week_end + IS456 delta
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 3: validate_and_map IS456 — strip_week = week_end + IS456 delta")
print(SEP)

df3 = make_df()
col_map3 = make_col_map(df3)
result3, _ = validate_and_map(df3, col_map3, stripping_standard="IS456")

expected_strip = [
    # F01 ALU-600: week_end=2, delta=2 -> strip=4
    4,
    # F02 ALU-600: week_end=3, delta=2 -> strip=5
    5,
    # F03 ALU-450: week_end=4, delta=1 -> strip=5
    5,
    # F04 ALU-450: week_end=5, delta=1 -> strip=6
    6,
    # F05 H20-beam: week_end=6, delta=2 -> strip=8
    8,
    # F06 H20-beam: week_end=7, delta=2 -> strip=9
    9,
]
for i, (got, exp) in enumerate(zip(result3["strip_week"].tolist(), expected_strip)):
    assert got == exp, (
        f"FAIL Test 3: row {i} expected strip_week={exp}, got {got}"
    )
    print(f"  PASS F{i+1:02d}: strip_week={got}")


# ══════════════════════════════════════════════════════════════════
# Test 4 — validate_and_map ACI347R-14: strip_week = week_end + 2
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 4: validate_and_map ACI347R-14 — strip_week = week_end + 2")
print(SEP)

df4 = make_df()
col_map4 = make_col_map(df4)
result4, _ = validate_and_map(df4, col_map4, stripping_standard="ACI347R-14")

for i, row in result4.iterrows():
    expected_sw = row["week_end"] + 2
    assert row["strip_week"] == expected_sw, (
        f"FAIL Test 4: row {i} expected strip_week={expected_sw}, got {row['strip_week']}"
    )
    print(f"  PASS F{i+1:02d}: strip_week={row['strip_week']} (week_end={row['week_end']}+2)")


# ══════════════════════════════════════════════════════════════════
# Test 5 — User-provided strip_week preserved unchanged (both standards)
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 5: User-provided strip_week preserved unchanged (both standards)")
print(SEP)

df5 = make_df(with_strip_week=True)
col_map5 = make_col_map(df5)
col_map5["strip_week"] = "strip_week"

user_strip = df5["strip_week"].tolist()

for std in ["IS456", "ACI347R-14"]:
    res, _ = validate_and_map(df5.copy(), col_map5, stripping_standard=std)
    for i, (got, exp) in enumerate(zip(res["strip_week"].tolist(), user_strip)):
        assert got == exp, (
            f"FAIL Test 5 ({std}): row {i} user strip_week={exp} overwritten to {got}"
        )
    print(f"  PASS ({std}): all {len(user_strip)} user strip_weeks preserved")


# ══════════════════════════════════════════════════════════════════
# Test 6 — Unknown SKU gets DEFAULT_STRIP_WEEKS_IS456 = 2
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 6: Unknown SKU defaults to 2 weeks under IS456")
print(SEP)

df6 = pd.DataFrame([{
    "floor_id":      "F99",
    "week_start":    1,
    "week_end":      2,
    "slab_area_m2":  100.0,
    "wall_length_m": 30.0,
    "col_count":     8,
    "panel_type":    "UNKNOWN-SKU",
}])
delta6 = get_strip_weeks_is456(df6)
assert delta6.iloc[0] == DEFAULT_STRIP_WEEKS_IS456, (
    f"FAIL Test 6: expected {DEFAULT_STRIP_WEEKS_IS456}, got {delta6.iloc[0]}"
)
print(f"PASS: UNKNOWN-SKU -> delta={delta6.iloc[0]} (DEFAULT_STRIP_WEEKS_IS456={DEFAULT_STRIP_WEEKS_IS456})")


# ══════════════════════════════════════════════════════════════════
# Test 7 — SKU_STRIP_WEEKS_IS456 constant values correct
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 7: SKU_STRIP_WEEKS_IS456 constants: ALU-600=2, ALU-450=1, H20-beam=2")
print(SEP)

assert SKU_STRIP_WEEKS_IS456["ALU-600"]  == 2, "FAIL Test 7: ALU-600 should be 2"
assert SKU_STRIP_WEEKS_IS456["ALU-450"]  == 1, "FAIL Test 7: ALU-450 should be 1"
assert SKU_STRIP_WEEKS_IS456["H20-beam"] == 2, "FAIL Test 7: H20-beam should be 2"
print(f"PASS: {SKU_STRIP_WEEKS_IS456}")


# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("All assertions pass")
print(SEP)
sys.exit(0)
