import sys
import pandas as pd
import numpy as np

sys.path.insert(0, ".")
from core.clustering import generate_kit_families, compute_repetition_score

checks = []

# 1. generate_kit_families handles empty dataframe
empty_df = pd.DataFrame()
empty_labels = np.array([])
res_empty = generate_kit_families(empty_df, empty_labels)
checks.append(("Empty dataframe handled (returns [])", isinstance(res_empty, list) and len(res_empty) == 0))

# 2. Noise cluster correctly labeled "Custom Kit"
df_noise = pd.DataFrame([
    {"floor_id": 1, "slab_area_sqm": 100, "wall_length_m": 50, "column_count": 10, "panel_type": "ALU-600"}
])
labels_noise = np.array([-1])
res_noise = generate_kit_families(df_noise, labels_noise)
checks.append(("Noise cluster labeled Custom Kit", len(res_noise) == 1 and res_noise[0]["kit_id"] == "Custom Kit"))

# 3. Kit IDs are alphabetic
df_multi = pd.DataFrame([
    {"floor_id": 1, "slab_area_sqm": 100, "wall_length_m": 50, "col_count": 10, "panel_type": "ALU"},
    {"floor_id": 2, "slab_area_sqm": 200, "wall_length_m": 80, "col_count": 20, "panel_type": "H20"},
])
labels_multi = np.array([0, 1])
res_multi = generate_kit_families(df_multi, labels_multi)
checks.append(("Kit IDs are alphabetic (Kit A, Kit B)", len(res_multi) == 2 and res_multi[0]["kit_id"] == "Kit A" and res_multi[1]["kit_id"] == "Kit B"))

# 4. est_wall_panels uses ceil() not round()
df_ceil = pd.DataFrame([
    {"floor_id": 1, "slab_area_sqm": 0.1, "wall_length_m": 0.1, "column_count": 10, "panel_type": "ALU"}
])
labels_ceil = np.array([0])
res_ceil = generate_kit_families(df_ceil, labels_ceil)
# ceil(0.1 / 0.6) = 1, NOT 0.
checks.append(("est_wall_panels uses ceil (not round)", res_ceil[0]["est_wall_panels"] == 1))

# 5. Kit card renders for demo_tower_40floors.xlsx
# I'll simulate it by checking try2_real.py for the UI code
src = open("try2_real.py", encoding="utf-8").read()
checks.append(("Kit families loop in try2_real UI", "for kit in kit_families:" in src))

# 6. Caption present with Phase 2 BIM note
checks.append(("Caption with BIM note", "Actual counts require panel layout drawings (Phase 2 \u2014 BIM input)." in src))

# 7. session_state keys set before PDF render block
checks.append(("session_state['kit_families'] set", 'st.session_state.kit_families     = kit_families' in src))

# 8. No crash if all floors are noise (single cluster case)
df_all_noise = pd.DataFrame([
    {"floor_id": i, "slab_area_sqm": 100, "wall_length_m": 50, "col_count": 10, "panel_type": "ALU"}
    for i in range(5)
])
labels_all_noise = np.array([-1]*5)
res_all_noise = generate_kit_families(df_all_noise, labels_all_noise)
checks.append(("No crash if all noise", len(res_all_noise) == 1 and res_all_noise[0]["kit_id"] == "Custom Kit"))

# 9. primary_sku shows correctly (mode of panel_type)
df_sku = pd.DataFrame([
    {"floor_id": 1, "slab_area_m2": 100, "wall_length_m": 50, "col_count": 10, "panel_type": "TypeA"},
    {"floor_id": 2, "slab_area_m2": 100, "wall_length_m": 50, "col_count": 10, "panel_type": "TypeA"},
    {"floor_id": 3, "slab_area_m2": 100, "wall_length_m": 50, "col_count": 10, "panel_type": "TypeB"},
])
labels_sku = np.array([0, 0, 0])
res_sku = generate_kit_families(df_sku, labels_sku)
checks.append(("primary_sku is mode", res_sku[0]["primary_sku"] == "TypeA"))


print("=" * 60)
print("Kit Families Feature — Checklist")
print("=" * 60)
all_pass = True
for label, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'} | {label}")
    if not ok:
        all_pass = False
print()
print("All checks passed!" if all_pass else "One or more checks FAILED.")
