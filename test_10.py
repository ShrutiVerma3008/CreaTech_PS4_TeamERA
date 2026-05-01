import pandas as pd, sys
sys.path.insert(0, '.')
try:
    from freeze_guard import (compute_design_freeze,
                               identify_unstable_floors,
                               estimate_rework_cost,
                               get_procurement_recommendation)
except ImportError:
    from core.freeze_guard import (compute_design_freeze,
                                    identify_unstable_floors,
                                    estimate_rework_cost,
                                    get_procurement_recommendation)

# Test A: stable
df_stable = pd.DataFrame({
    'floor_id':      ['F01','F02','F03','F04','F05'],
    'slab_area_m2':  [850, 860, 855, 858, 845],
    'wall_length_m': [124, 126, 125, 124, 123],
    'col_count':     [18,  18,  18,  18,  18 ]
})
freeze_s  = compute_design_freeze(df_stable)
unstable_s = identify_unstable_floors(df_stable)
print(f'Test A — DI: {freeze_s["DI"]:.1f}%, '
      f'Status: {freeze_s["status"]}, '
      f'Unstable floors: {len(unstable_s)}')
assert freeze_s['status'] == 'SAFE'
assert len(unstable_s) == 0, f'Expected 0, got {len(unstable_s)}'

# Test B: 2 floors 3x larger
df_unstable = pd.DataFrame({
    'floor_id':      ['F01','F02','F03','F04','F05'],
    'slab_area_m2':  [850, 860, 2600, 2700, 845],
    'wall_length_m': [124, 126, 125,  124,  123],
    'col_count':     [18,  18,  18,   18,   18 ]
})
freeze_u   = compute_design_freeze(df_unstable)
unstable_u = identify_unstable_floors(df_unstable)
unstable_ids = list(set(u['floor_id'] for u in unstable_u))
print(f'Test B — DI: {freeze_u["DI"]:.1f}%, '
      f'Status: {freeze_u["status"]}, '
      f'Unstable floors: {unstable_ids}')
assert freeze_u['status'] == 'HALT'
assert ('F03' in unstable_ids or 'F04' in unstable_ids), \
    f'F03/F04 should be flagged, got: {unstable_ids}'

print('Both tests passed')
