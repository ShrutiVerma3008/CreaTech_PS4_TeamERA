import pandas as pd
import numpy as np

def aggregate_schedule(df_floors):
    """
    Given a dataframe with floor-level schedule:
    [floor_id, week_start, week_end, slab_area_m2, wall_length_m, col_count, ...]
    Aggregate into a weekly demand schedule.
    """
    all_weeks = sorted(list(set(df_floors["week_start"].tolist() + df_floors["week_end"].tolist())))
    if not all_weeks:
        return pd.DataFrame()
    
    min_week = min(all_weeks)
    max_week = max(all_weeks)
    
    weekly_data = []
    for w in range(min_week, max_week + 1):
        # Floors active in week w
        active = df_floors[(df_floors["week_start"] <= w) & (df_floors["week_end"] >= w)]
        
        # In a real scenario, demand is more complex (e.g. wall panels at start, slab at end)
        # For simplicity, we aggregate the physical requirements of active floors.
        # We'll use a simple heuristic to convert area/length to panel demand
        # (similar to generate_building_data in try2_real.py)
        
        wall_demand = int(active["wall_length_m"].sum() / 8.5) # Example heuristic
        slab_demand = int(active["slab_area_m2"].sum() / 12.0)
        col_demand  = int(active["col_count"].sum())
        
        weekly_data.append({
            "week": w,
            "wall_panels_demand": max(1, wall_demand),
            "slab_panels_demand": max(1, slab_demand),
            "col_panels_demand":  max(1, col_demand)
        })
    
    return pd.DataFrame(weekly_data)

# Test with the demo file
file_path = r"d:\sem_6\creaTech\try1\data\demo_tower_40floors.xlsx"
df = pd.read_excel(file_path)

# Map columns (assuming exact match for now)
df_schedule = aggregate_schedule(df)
print("Aggregated Schedule Preview:")
print(df_schedule.head(10))
