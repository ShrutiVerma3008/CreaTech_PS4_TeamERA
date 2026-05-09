"""
scratch/verify_gap4.py
Standalone verification for Gap 4 — compute_sensitivity_analysis.
Run: python scratch/verify_gap4.py
Expected: exits code 0, prints "All assertions pass."
"""
import sys, math
sys.path.insert(0, ".")
import pandas as pd
from core.lp_optimizer import compute_sensitivity_analysis

# ── Minimal mock schedule: 10 floors, 3 SKUs ─────────────────────────────────
df = pd.DataFrame({
    "week":                [1,  2,  3,  4,  5,  6,  7,  8,  9,  10],
    "wall_panels_demand":  [80, 85, 82, 78, 80, 88, 84, 76, 82, 80],
    "slab_panels_demand":  [60, 65, 62, 58, 60, 66, 62, 58, 60, 60],
    "col_panels_demand":   [18, 20, 19, 17, 18, 21, 19, 17, 18, 18],
})

c_p, c_h, c_i = 15000, 500, 2000

# ── Call the function ─────────────────────────────────────────────────────────
result = compute_sensitivity_analysis(df, c_p, c_h, c_i)
print(result.to_string(index=False))
print()

# ── 1. Exactly 7 rows ─────────────────────────────────────────────────────────
assert len(result) == 7, f"FAIL: expected 7 rows, got {len(result)}"

# ── 2. Correct columns ────────────────────────────────────────────────────────
expected_cols = [
    "scenario", "optimised_cr", "zero_baseline_cr",
    "experienced_baseline_cr", "savings_vs_zero_pct", "savings_vs_experienced_pct"
]
assert list(result.columns) == expected_cols, \
    f"FAIL columns: {list(result.columns)}"

# ── 3. Base Case savings_vs_zero_pct > 0 ─────────────────────────────────────
base = result[result["scenario"] == "Base Case"].iloc[0]
assert base["savings_vs_zero_pct"] > 0, \
    f"FAIL Base Case savings_vs_zero_pct={base['savings_vs_zero_pct']}"

# ── 4. No scenario has savings_vs_zero_pct < 0 ───────────────────────────────
non_nan = result["savings_vs_zero_pct"].dropna()
assert (non_nan >= 0).all(), \
    f"FAIL: negative savings_vs_zero_pct in: {result[result['savings_vs_zero_pct'] < 0]}"

# ── 5. Savings range is between 8% and 70% (credible, not cherry-picked) ─────
svz_min = non_nan.min()
svz_max = non_nan.max()
assert svz_min >= 8.0,  f"FAIL: savings_vs_zero_pct min {svz_min:.1f}% < 8%"
assert svz_max <= 70.0, f"FAIL: savings_vs_zero_pct max {svz_max:.1f}% > 70%"

# ── 6. All 6 columns present in every row ────────────────────────────────────
for col in expected_cols:
    assert col in result.columns, f"FAIL: missing column '{col}'"

# ── 7. optimised_cr < zero_baseline_cr for all non-NaN rows ──────────────────
for _, row in result.dropna(subset=["optimised_cr"]).iterrows():
    assert row["optimised_cr"] <= row["zero_baseline_cr"], \
        f"FAIL: optimised_cr {row['optimised_cr']} > zero_baseline_cr {row['zero_baseline_cr']} in {row['scenario']}"

# ── 8. experienced_baseline_cr < zero_baseline_cr (35% reuse cheaper) ───────
for _, row in result.iterrows():
    assert row["experienced_baseline_cr"] <= row["zero_baseline_cr"], \
        f"FAIL: exp_baseline > zero_baseline in {row['scenario']}"

print(f"Savings vs zero:  {svz_min:.1f}% – {svz_max:.1f}%")
print(f"Scenarios: {list(result['scenario'])}")
print()
print("All assertions pass.")
