"""
scratch/verify_gap2.py
Standalone verification for Gap 2 — compute_experienced_planner_baseline.
Run: python scratch/verify_gap2.py
Expected: exits code 0, prints "All assertions pass."
"""
import math, sys
sys.path.insert(0, ".")

# ── 1. Import must succeed ────────────────────────────────────────────────────
from core.lp_optimizer import compute_experienced_planner_baseline, compute_baseline
import pandas as pd

# ── 2. Mock schedule: 5 floors × 2 SKUs ─────────────────────────────────────
df = pd.DataFrame({
    "week": [1, 2, 3, 4, 5],
    "wall_panels_demand": [100, 110, 105, 95, 100],
    "slab_panels_demand": [80,  85,  82,  78,  80],
    "col_panels_demand":  [20,  22,  20,  18,  20],
})
c_p        = 15000
reuse_rate = 0.35

# ── 3. Call ───────────────────────────────────────────────────────────────────
result = compute_experienced_planner_baseline(df, c_p, reuse_rate=reuse_rate)

print("compute_experienced_planner_baseline() output:")
for k, v in result.items():
    print(f"  {k}: {v}")

# ── 4. Assertions ─────────────────────────────────────────────────────────────

# 4a. All 5 keys exist
required_keys = {"total_demand", "panels_reused", "panels_purchased", "cost", "reuse_rate"}
assert required_keys == set(result.keys()), f"FAIL: missing keys {required_keys - set(result.keys())}"

# 4b. total_demand correct
total_demand_expected = (
    sum([100, 110, 105, 95, 100]) +
    sum([80, 85, 82, 78, 80]) +
    sum([20, 22, 20, 18, 20])
)
assert result["total_demand"] == total_demand_expected, \
    f"FAIL total_demand: {result['total_demand']} != {total_demand_expected}"

# 4c. panels_reused = floor(total_demand * reuse_rate)
expected_reused = math.floor(total_demand_expected * reuse_rate)
assert result["panels_reused"] == expected_reused, \
    f"FAIL panels_reused: {result['panels_reused']} != {expected_reused}"

# 4d. panels_purchased + panels_reused == total_demand
assert result["panels_purchased"] + result["panels_reused"] == result["total_demand"], \
    f"FAIL: purchased {result['panels_purchased']} + reused {result['panels_reused']} != total {result['total_demand']}"

# 4e. cost = panels_purchased * c_p
expected_cost = result["panels_purchased"] * c_p
assert result["cost"] == float(expected_cost), \
    f"FAIL cost: {result['cost']} != {expected_cost}"

# 4f. cost < zero-reuse baseline (LP is always cheaper than zero-reuse)
zero_baseline = compute_baseline(df, c_p)
assert result["cost"] < zero_baseline, \
    f"FAIL: experienced cost {result['cost']} >= zero-reuse baseline {zero_baseline}"

# 4g. reuse_rate stored correctly
assert result["reuse_rate"] == reuse_rate, f"FAIL reuse_rate stored incorrectly"

# 4h. ValueError on bad reuse_rate
try:
    compute_experienced_planner_baseline(df, c_p, reuse_rate=1.5)
    assert False, "FAIL: should have raised ValueError for reuse_rate=1.5"
except ValueError:
    pass  # expected

print()
print(f"  zero_baseline:       Rs {zero_baseline/1e7:.4f} Cr")
print(f"  experienced cost:    Rs {result['cost']/1e7:.4f} Cr")
print(f"  savings vs zero:     Rs {(zero_baseline - result['cost'])/1e7:.4f} Cr  ({(1 - result['cost']/zero_baseline)*100:.1f}%)")
print()
print("All assertions pass.")
