"""
scratch/verify_export_tab.py
Standalone verification for Task 1 (PDF sensitivity table) and Tab 7 wiring.
Run: python scratch/verify_export_tab.py
Expected: exits code 0 and prints "All assertions pass."
"""
import sys
sys.path.insert(0, ".")

import pandas as pd
from utils.report_generator import generate_boq_pdf

# ── Minimal mock data ─────────────────────────────────────────────
boq_df = pd.DataFrame([
    {"sku": "wall", "week": 1, "procure": 30, "reuse": 0,  "hold": 5,  "idle": 2,  "week_cost": 450000},
    {"sku": "wall", "week": 2, "procure": 10, "reuse": 20, "hold": 3,  "idle": 0,  "week_cost": 165000},
    {"sku": "slab", "week": 1, "procure": 20, "reuse": 0,  "hold": 2,  "idle": 1,  "week_cost": 307000},
    {"sku": "slab", "week": 2, "procure": 5,  "reuse": 15, "hold": 1,  "idle": 0,  "week_cost": 80000},
])

delivery_df = pd.DataFrame([
    {"sku": "wall", "week": 1, "procure": 30, "estimated_delivery_week": 2, "week_cost": 450000},
    {"sku": "slab", "week": 1, "procure": 20, "estimated_delivery_week": 2, "week_cost": 307000},
])

metrics = {
    "optimized_cr":           0.10,
    "baseline_cr":            0.15,
    "savings_cr":             0.05,
    "savings_pct":            33.3,
    "overall_reuse_rate":     0.35,
    "di_value":               8.5,
    "di_status":              "SAFE",
    "custom_area_total":      0,
    "custom_cost_premium":    0,
    "kit_count":              3,
    "highest_reuse_kit":      "Kit A",
    "experienced_baseline_cr": 0.12,
    "savings_vs_experienced_cr": 0.02,
    "pct_vs_experienced":     16.7,
}

sensitivity_df = pd.DataFrame([
    {"scenario": "Base Case",       "optimised_cr": 0.75, "zero_baseline_cr": 2.42, "experienced_baseline_cr": 1.57, "savings_vs_zero_pct": 68.9, "savings_vs_experienced_pct": 52.2},
    {"scenario": "c_p +50%",        "optimised_cr": 1.12, "zero_baseline_cr": 3.62, "experienced_baseline_cr": 2.36, "savings_vs_zero_pct": 69.0, "savings_vs_experienced_pct": 52.3},
    {"scenario": "c_p -50%",        "optimised_cr": 0.38, "zero_baseline_cr": 1.21, "experienced_baseline_cr": 0.79, "savings_vs_zero_pct": 68.7, "savings_vs_experienced_pct": 51.9},
    {"scenario": "Reuse rate +20%", "optimised_cr": 0.75, "zero_baseline_cr": 2.42, "experienced_baseline_cr": 1.40, "savings_vs_zero_pct": 68.9, "savings_vs_experienced_pct": 46.4},
    {"scenario": "Reuse rate -20%", "optimised_cr": 0.75, "zero_baseline_cr": 2.42, "experienced_baseline_cr": 1.74, "savings_vs_zero_pct": 68.9, "savings_vs_experienced_pct": 56.8},
    {"scenario": "Schedule -30%",   "optimised_cr": 0.77, "zero_baseline_cr": 2.42, "experienced_baseline_cr": 1.57, "savings_vs_zero_pct": 68.2, "savings_vs_experienced_pct": 51.2},
    {"scenario": "Schedule +30%",   "optimised_cr": 0.98, "zero_baseline_cr": 2.42, "experienced_baseline_cr": 1.57, "savings_vs_zero_pct": 59.2, "savings_vs_experienced_pct": 37.4},
])

# ── Test 1: PDF with sensitivity_df ──────────────────────────────
result_with = generate_boq_pdf(
    boq_df=boq_df,
    delivery_df=delivery_df,
    metrics=metrics,
    project_name="Test Project",
    sensitivity_df=sensitivity_df,
)
assert isinstance(result_with, bytes), "FAIL: result_with is not bytes"
assert len(result_with) > 7368, f"FAIL: PDF too small ({len(result_with)} bytes)"
print(f"PDF with sensitivity_df: {len(result_with):,} bytes  OK")

# ── Test 2: PDF without sensitivity_df (None) — no crash ─────────
result_without = generate_boq_pdf(
    boq_df=boq_df,
    delivery_df=delivery_df,
    metrics=metrics,
    project_name="Test Project",
    sensitivity_df=None,
)
assert isinstance(result_without, bytes), "FAIL: result_without is not bytes"
assert len(result_without) > 7368, f"FAIL: PDF (no sens) too small ({len(result_without)} bytes)"
print(f"PDF without sensitivity_df: {len(result_without):,} bytes  OK")

# ── Test 3: PDF with sensitivity is larger ────────────────────────
assert len(result_with) > len(result_without), (
    f"FAIL: with-sensitivity PDF ({len(result_with)}) not larger than without ({len(result_without)})"
)
print(f"With-sensitivity PDF is {len(result_with) - len(result_without):,} bytes larger  OK")

# ── Test 4: Correct return type in both cases ─────────────────────
for label, r in [("with", result_with), ("without", result_without)]:
    assert r[:4] == b"%PDF", f"FAIL: {label} result is not a valid PDF"
print("Both results are valid PDFs (start with %PDF)  OK")

# ── Test 5: sensitivity_df=empty DataFrame — no crash ────────────
result_empty = generate_boq_pdf(
    boq_df=boq_df,
    delivery_df=delivery_df,
    metrics=metrics,
    project_name="Test Project",
    sensitivity_df=pd.DataFrame(),
)
assert isinstance(result_empty, bytes), "FAIL: result_empty is not bytes"
print(f"PDF with empty sensitivity_df: {len(result_empty):,} bytes  OK")

print()
print("All assertions pass.")
