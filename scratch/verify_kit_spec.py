"""
Standalone verification for generate_kit_specification — Gap 1 closure check.
Run: python scratch/verify_kit_spec.py
"""
import sys
sys.path.insert(0, ".")
import numpy as np
import pandas as pd
from core.clustering import generate_kit_specification, DEFAULT_SKU_COVERAGE

# ── Build a minimal fake kit_families list ───────────────────────────────────
fake_kit_families = [
    {
        "kit_id":        "Kit A",
        "cluster_id":    0,
        "floor_ids":     ["F01", "F02", "F05", "F08", "F10", "F12"],
        "floor_count":   6,
        "avg_slab_area": 850.0,
        "avg_wall_length": 124.0,
        "avg_col_count": 18.0,
        "reuse_potential": "HIGH",
        "primary_sku": "ALU-600",
    },
    {
        "kit_id":        "Custom Kit",
        "cluster_id":    -1,
        "floor_ids":     ["F00", "F39"],
        "floor_count":   2,
        "avg_slab_area": 620.0,
        "avg_wall_length": 90.0,
        "avg_col_count": 12.0,
        "reuse_potential": "LOW",
        "primary_sku": "ALU-450",
    },
]

# ── Build a minimal floor DataFrame ──────────────────────────────────────────
fake_df = pd.DataFrame([
    {"floor_id": "F01", "slab_area_sqm": 850.0},
    {"floor_id": "F02", "slab_area_sqm": 860.0},
    {"floor_id": "F05", "slab_area_sqm": 840.0},
    {"floor_id": "F08", "slab_area_sqm": 855.0},
    {"floor_id": "F10", "slab_area_sqm": 845.0},
    {"floor_id": "F12", "slab_area_sqm": 850.0},
    {"floor_id": "F00", "slab_area_sqm": 620.0},
    {"floor_id": "F39", "slab_area_sqm": 620.0},
])

# ── Call the function ─────────────────────────────────────────────────────────
result = generate_kit_specification(fake_kit_families, fake_df)

print("=" * 60)
print("generate_kit_specification() — output")
print("=" * 60)
print(result.to_string(index=False))
print()

# ── Assertions ───────────────────────────────────────────────────────────────
assert list(result.columns) == ["kit_id", "sku", "avg_area_m2", "panel_count", "buffer_panels", "total_panels"], \
    f"FAIL: unexpected columns {list(result.columns)}"

# Kit A, ALU-600: avg_area=850, coverage=0.72 → panel_count=ceil(850/0.72)=1181
kit_a_alu600 = result[(result["kit_id"] == "Kit A") & (result["sku"] == "ALU-600")].iloc[0]
expected_panels = int(np.ceil(850.0 / 0.72))
expected_buffer = int(np.ceil(expected_panels * 0.10))
expected_total  = expected_panels + expected_buffer

assert kit_a_alu600["panel_count"]   == expected_panels, f"FAIL panel_count: {kit_a_alu600['panel_count']} != {expected_panels}"
assert kit_a_alu600["buffer_panels"] == expected_buffer, f"FAIL buffer_panels: {kit_a_alu600['buffer_panels']} != {expected_buffer}"
assert kit_a_alu600["total_panels"]  == expected_total,  f"FAIL total_panels: {kit_a_alu600['total_panels']} != {expected_total}"

# Custom Kit: avg_area=620, same checks
ck_alu600 = result[(result["kit_id"] == "Custom Kit") & (result["sku"] == "ALU-600")].iloc[0]
ck_panels = int(np.ceil(620.0 / 0.72))
ck_buffer = int(np.ceil(ck_panels * 0.10))
assert ck_alu600["panel_count"]   == ck_panels, f"FAIL Custom Kit panel_count"
assert ck_alu600["buffer_panels"] == ck_buffer, f"FAIL Custom Kit buffer_panels"

# Empty input should return empty DataFrame with correct columns
empty_result = generate_kit_specification([], fake_df)
assert empty_result.empty and list(empty_result.columns) == ["kit_id", "sku", "avg_area_m2", "panel_count", "buffer_panels", "total_panels"], \
    "FAIL: empty input should return empty DataFrame with correct columns"

# Missing area column should return empty DataFrame
no_area_df = pd.DataFrame([{"floor_id": "F01"}])
no_area_result = generate_kit_specification(fake_kit_families, no_area_df)
assert no_area_result.empty, "FAIL: no area column should return empty DataFrame"

print("=" * 60)
print("ALL ASSERTIONS PASSED — Gap 1 closure verified.")
print("=" * 60)
print()
print("DEFAULT_SKU_COVERAGE:", DEFAULT_SKU_COVERAGE)
