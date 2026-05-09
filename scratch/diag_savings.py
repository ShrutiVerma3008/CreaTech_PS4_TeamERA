import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '.')

# Replicate the synthetic schedule exactly as the app does
np.random.seed(42)
n_floors = 20
floors_per_week = max(1, n_floors // 18)
weeks = []
base_slab = 850
df_floors_temp = pd.DataFrame({
    'floor_id': range(n_floors),
    'slab_area_sqm': [base_slab] * n_floors
})
for w in range(1, 53):
    active_start = min(int((w-1) * n_floors / 52), n_floors - 1)
    active_end   = min(active_start + floors_per_week, n_floors)
    active_floors = list(range(active_start, active_end))
    if not active_floors:
        active_floors = [active_start]
    total_slab = df_floors_temp.loc[df_floors_temp.floor_id.isin(active_floors), 'slab_area_sqm'].sum()
    wall_panels  = int(total_slab / 8.5  * np.random.uniform(0.95, 1.05))
    slab_panels  = int(total_slab / 12.0 * np.random.uniform(0.95, 1.05))
    col_panels   = int(total_slab / 18.0 * np.random.uniform(0.95, 1.05))
    weeks.append({
        'week': w,
        'wall_panels_demand': max(10, wall_panels),
        'slab_panels_demand': max(8,  slab_panels),
        'col_panels_demand':  max(5,  col_panels),
    })
df_sched = pd.DataFrame(weeks)

print("Schedule columns:", list(df_sched.columns))
print("Sum wall demand:", df_sched['wall_panels_demand'].sum())
print("Sum slab demand:", df_sched['slab_panels_demand'].sum())
print("Sum col  demand:", df_sched['col_panels_demand'].sum())

from core.lp_optimizer import compute_baseline, run_sku_optimizer

c_p = 15000
baseline = compute_baseline(df_sched, c_p)
print(f"\ncompute_baseline => Rs {baseline/1e7:.4f} Cr")

result = run_sku_optimizer(df_sched, None, c_p=c_p, c_h=500, c_i=800)
print(f"status:           {result['status']}")
print(f"optimized_total:  Rs {result['optimized_total']/1e7:.4f} Cr")
print(f"baseline_total:   Rs {result['baseline_total']/1e7:.4f} Cr")
print(f"savings:          Rs {result['savings']/1e7:.4f} Cr")
print(f"savings_pct:      {result['savings_pct']:.2f}%")
print(f"opt_total alias:  Rs {result.get('opt_total',0)/1e7:.4f} Cr")
print(f"trad_total alias: Rs {result.get('trad_total',0)/1e7:.4f} Cr")
