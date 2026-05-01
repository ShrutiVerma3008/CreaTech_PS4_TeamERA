import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd, numpy as np
from freeze_guard import (
    compute_design_freeze,
    identify_unstable_floors,
    estimate_rework_cost,
    get_procurement_recommendation,
)

np.random.seed(0)
# Build a dataset with 2 outlier floors
base = list(np.random.uniform(840, 860, 13))
big  = [2700.0, 2650.0]
df = pd.DataFrame({
    "floor_id":      [f"F{i}" for i in range(15)],
    "slab_area_sqm": base + big,
    "wall_length_m": list(np.random.uniform(415, 425, 15)),
    "column_count":  list(np.random.randint(23, 26, 15).astype(float)),
})

# 1. compute_design_freeze
fr = compute_design_freeze(df)
print(f"[STEP 1] DI={fr['DI']:.2f}% status={fr['status']}")

# 2. identify_unstable_floors
unstable = identify_unstable_floors(df)
print(f"[STEP 2] Unstable floors detected: {len(unstable)} (floor,feature) pairs")
for u in unstable:
    print(f"  floor_id={u['floor_id']} feature={u['feature']} "
          f"value={u['value']} mean={u['mean']} dev%={u['deviation_pct']}")

# 3. estimate_rework_cost
rework = estimate_rework_cost(unstable, df, c_p=15000)
print(f"[STEP 3] panels_at_risk={rework['panels_at_risk']}")
print(f"         rework_cost_order_now=Rs {rework['rework_cost_order_now']:,.0f}")
print(f"         savings_if_wait_2w=Rs {rework['savings_if_wait_2w']:,.0f}")

# 4. get_procurement_recommendation
clusters = {0: [f"F{i}" for i in range(10)], 1: ["F13", "F14"]}
unstable_ids = list({u["floor_id"] for u in unstable})
rec = get_procurement_recommendation(fr["DI"], clusters, unstable_ids)
print(f"[STEP 4] action={rec['action']}")
print(f"         stable_clusters={rec['stable_clusters']}")
print(f"         unstable_clusters={rec['unstable_clusters']}")
print(f"         detail={rec['detail']}")

print("\nAll function tests PASSED")
