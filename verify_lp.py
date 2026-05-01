import pandas as pd
import numpy as np
from core.lp_optimizer import run_sku_optimizer, compute_baseline

def test_pipeline():
    print("--- CHECK 12: Full Pipeline Run (Optimized) ---")
    try:
        xls = pd.ExcelFile("formoptix_real_project.xlsx")
        df_floors    = pd.read_excel(xls, "floors")
        df_schedule  = pd.read_excel(xls, "schedule")

        # Mock stripping schedule and panel counts to trigger reuse
        # Without these, optimized == baseline.
        df_floors["strip_week"] = [max(1, i % 10) for i in range(len(df_floors))]
        df_floors["wall_panels"] = 50
        df_floors["slab_panels"] = 30
        df_floors["col_panels"]  = 10

        c_p, c_h, c_i = 15000, 500, 800

        print(f"Schedule columns: {df_schedule.columns.tolist()}")
        print("Mocked floor-level strip weeks and panel counts for reuse derivation.")
        
        results = run_sku_optimizer(df_schedule, df_floors, c_p, c_h, c_i)

        print(f"Status: {results['status']}")
        if "error" in results:
            print(f"Error: {results['error']}")
            return

        opt   = results['optimized_total']
        base  = results['baseline_total']
        saved = results['savings']
        pct   = results['savings_pct']
        print(f"Optimized Total : Rs {opt/1e7:.4f} Cr")
        print(f"Baseline  Total : Rs {base/1e7:.4f} Cr")
        print(f"Savings         : Rs {saved/1e7:.4f} Cr  ({pct:.2f}%)")
        print(f"Rows in boq_results: {len(results['boq_results'])}")
        
        # This should now be True because reuse reduces procurement.
        print(f"CONFIRMED: optimized < baseline: {opt < base}")

        print("\n--- CHECK 6: First 3 rows of boq_results ---")
        for i, row in enumerate(results['boq_results'][:3]):
            calc = c_p * row['procure'] + c_h * row['hold'] + c_i * row['idle']
            ok   = abs(calc - row['week_cost']) < 1
            print(f"  Row {i}: {row}")
            print(f"    Cost check: {c_p}×{row['procure']} + {c_h}×{row['hold']} + {c_i}×{row['idle']} = {calc}  | stored={row['week_cost']}  MATCH={ok}")

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
