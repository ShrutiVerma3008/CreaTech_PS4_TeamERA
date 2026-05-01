import pandas as pd
import numpy as np
from utils.demand_calc import build_reuse_matrix
from core.clustering import compute_repetition_score
from utils.data_loader import validate_and_map

print("\n--- CHECK 10 ---")
try:
    xls = pd.ExcelFile("formoptix_real_project.xlsx")
    df_floors = pd.read_excel(xls, "floors")
    df_schedule = pd.read_excel(xls, "schedule")
    
    # Need to merge schedule data before validating, similar to try2_real.py logic
    df_floors = df_floors.merge(df_schedule[["floor_id", "week_start", "week_end", "strip_week"]], on="floor_id", how="left")
    
    col_map = {
        "floor_id": "floor_id",
        "week_start": "week_start",
        "week_end": "week_end",
        "strip_week": "strip_week",
        "slab_area_m2": "slab_area_sqm",
        "wall_length_m": "wall_length_m",
        "col_count": "column_count",
        "panel_type": "panel_type"
    }
    df_floors = validate_and_map(df_floors, col_map)
    
    res_df, rep_score, cluster_summary, rho_k_map, reuse_pairs, overall_reuse = compute_repetition_score(df_floors, transport_weeks=1)
    
    print("Clusters found:", len([k for k in res_df["cluster"].unique() if k != -1]))
    print("Noise floors:", len(res_df[res_df["cluster"] == -1]))
    print("rho_k per cluster:")
    for k, v in rho_k_map.items():
        print(f"  Cluster {k}: {v:.3f}")
    print(f"Overall reuse rate: {overall_reuse:.1%}")
    print("Valid reuse pairs:", len(reuse_pairs))
except Exception as e:
    print("Error in Check 10:", e)
    import traceback
    traceback.print_exc()
