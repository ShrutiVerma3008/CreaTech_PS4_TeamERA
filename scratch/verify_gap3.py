"""
scratch/verify_gap3.py
Standalone verification for Gap 3 — compute_change_probability.
Run: python scratch/verify_gap3.py
Expected: exits code 0, prints "All assertions pass."
"""
import sys
sys.path.insert(0, ".")
import numpy as np
import pandas as pd
from freeze_guard import compute_change_probability

# ── Helper: minimal floor DataFrame ──────────────────────────────────────────
def make_df(slab_vals, wall_vals, col_vals):
    return pd.DataFrame({
        "slab_area_sqm": slab_vals,
        "wall_length_m": wall_vals,
        "col_count":     col_vals,
    })

# ── 1. Stable dataset — DI ~8%, all CVs well below 10% ───────────────────────
np.random.seed(0)
n = 15
df_stable = make_df(
    np.random.uniform(840, 860, n),    # CV ~0.8%
    np.random.uniform(118, 122, n),    # CV ~1.1%
    np.random.randint(17, 19, n).astype(float),  # CV ~4%
)
r_stable = compute_change_probability(df_stable, di_value=8.0)
print("STABLE:", r_stable)

assert r_stable["probability"] == "LOW",  f"FAIL stable probability: {r_stable['probability']}"
assert r_stable["pct"]         == 15,     f"FAIL stable pct: {r_stable['pct']}"
assert r_stable["sustained_above_10"] == False, "FAIL stable sustained_above_10"
assert "LOW" in r_stable["label"],         f"FAIL stable label: {r_stable['label']}"

# ── 2. Warning dataset — DI ~12%, only 1 CV above 10% (no upgrade) ───────────
df_warn_no_upgrade = make_df(
    np.concatenate([np.random.uniform(840, 870, 12), [1100, 1150, 1200]]),  # CV ~14% → 1 feature above 10
    np.random.uniform(118, 122, n),    # CV ~1%
    np.random.randint(17, 19, n).astype(float),  # CV ~4%
)
r_warn_no_up = compute_change_probability(df_warn_no_upgrade, di_value=12.0)
print("WARNING (no upgrade):", r_warn_no_up)

assert r_warn_no_up["probability"] == "MODERATE", f"FAIL warn_no_upgrade probability: {r_warn_no_up['probability']}"
assert r_warn_no_up["pct"]         == 45,          f"FAIL warn_no_upgrade pct: {r_warn_no_up['pct']}"

# ── 3. Warning dataset — DI ~12%, 2 CVs above 10% → upgrades to HIGH ─────────
df_warn_upgrade = make_df(
    np.concatenate([np.random.uniform(840, 870, 12), [1100, 1150, 1200]]),  # CV ~14% → above 10
    np.concatenate([np.random.uniform(118, 122, 12), [200, 210, 220]]),     # CV ~25% → above 10
    np.random.randint(17, 19, n).astype(float),  # CV low
)
r_warn_up = compute_change_probability(df_warn_upgrade, di_value=12.0)
print("WARNING (upgrade):", r_warn_up)

assert r_warn_up["sustained_above_10"] == True,  f"FAIL warn_upgrade sustained_above_10"
assert r_warn_up["probability"]        == "HIGH", f"FAIL warn_upgrade probability: {r_warn_up['probability']}"
assert r_warn_up["pct"]                == 78,     f"FAIL warn_upgrade pct: {r_warn_up['pct']}"

# ── 4. Halt dataset — DI ~20%, base HIGH (no upgrade needed) ──────────────────
df_halt = make_df(
    np.concatenate([np.random.uniform(840, 870, 12), [2500, 2600, 2700]]),
    np.concatenate([np.random.uniform(118, 122, 12), [300, 310, 320]]),
    np.concatenate([np.random.randint(17, 19, 12).astype(float), [40, 42, 44]]),
)
r_halt = compute_change_probability(df_halt, di_value=20.0)
print("HALT:", r_halt)

assert r_halt["probability"] == "HIGH", f"FAIL halt probability: {r_halt['probability']}"
assert r_halt["pct"]         == 78,     f"FAIL halt pct: {r_halt['pct']}"
assert "HIGH" in r_halt["label"],        f"FAIL halt label: {r_halt['label']}"

# ── 5. All 7 keys present ─────────────────────────────────────────────────────
required_keys = {"probability", "pct", "label", "sustained_above_10",
                 "cv_slab", "cv_wall", "cv_col"}
for r, name in [(r_stable, "stable"), (r_warn_no_up, "warn_no_up"),
                (r_warn_up, "warn_up"), (r_halt, "halt")]:
    missing = required_keys - set(r.keys())
    assert not missing, f"FAIL {name}: missing keys {missing}"

# ── 6. CV values are floats ≥ 0 ──────────────────────────────────────────────
for r, name in [(r_stable, "stable"), (r_halt, "halt")]:
    assert isinstance(r["cv_slab"], float) and r["cv_slab"] >= 0, f"FAIL {name} cv_slab"
    assert isinstance(r["cv_wall"], float) and r["cv_wall"] >= 0, f"FAIL {name} cv_wall"
    assert isinstance(r["cv_col"],  float) and r["cv_col"]  >= 0, f"FAIL {name} cv_col"

print()
print("All assertions pass.")
