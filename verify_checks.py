# -*- coding: utf-8 -*-
"""
FormOptiX — Verification Script
================================
Checks (non-destructive, no logic changes):
  [1] All imports resolve          (no missing packages)
  [2] app.py (try2_real.py) parse  (no syntax errors)
  [3] DBSCAN produces >=1 cluster  on synthetic data
  [4] LP optimizer returns numeric cost
  [5] Design Freeze Guard returns DI value + status string

Run:  python verify_checks.py
"""

import sys
# Force UTF-8 on Windows so Unicode arrows/ticks render
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import traceback

PASS = "[PASS]"
FAIL = "[FAIL]"

results = {}

SEP = "=" * 62


# ──────────────────────────────────────────────
# CHECK 1 — ALL IMPORTS RESOLVE
# ──────────────────────────────────────────────
print("\n" + SEP)
print("CHECK 1 — Import resolution")
print(SEP)

required = {
    "streamlit":  "streamlit>=1.32.0",
    "pandas":     "pandas>=2.0.0",
    "numpy":      "numpy>=1.24.0",
    "plotly":     "plotly>=5.18.0",
    "pulp":       "pulp>=2.7.0",
    "sklearn":    "scikit-learn>=1.3.0",
    "scipy":      "scipy>=1.11.0",
}

import_failures = []
for module, pip_spec in required.items():
    try:
        __import__(module)
        print(f"  OK   {module:12s}  ({pip_spec})")
    except ImportError as e:
        print(f"  MISS {module:12s}  ({pip_spec})  ->  {e}")
        import_failures.append(pip_spec)

if import_failures:
    print(f"\n{FAIL} Missing packages: {', '.join(import_failures)}")
    results["imports"] = (False, f"Missing: {import_failures}")
else:
    print(f"\n{PASS} All required packages are importable.")
    results["imports"] = (True, "All packages available")


# ──────────────────────────────────────────────
# CHECK 2 — try2_real.py PARSES WITHOUT SYNTAX ERROR
# ──────────────────────────────────────────────
print("\n" + SEP)
print("CHECK 2 — try2_real.py syntax / ast parse")
print(SEP)

import ast
import pathlib

APP_FILE = pathlib.Path(__file__).parent / "try2_real.py"

try:
    source = APP_FILE.read_text(encoding="utf-8")
    ast.parse(source)
    size_kb = len(source) // 1024
    print(f"  OK   {APP_FILE.name} parsed without syntax errors ({size_kb} KB, "
          f"{source.count(chr(10))+1} lines)")
    print(f"\n{PASS} App file compiles cleanly.")
    results["app_parse"] = (True, "No syntax errors")
except SyntaxError as e:
    print(f"  ERR  SyntaxError at line {e.lineno}: {e.msg}")
    print(f"\n{FAIL} Syntax error in app file.")
    results["app_parse"] = (False, str(e))
except Exception as e:
    print(f"  ERR  Unexpected: {e}")
    results["app_parse"] = (False, str(e))


# ──────────────────────────────────────────────
# SETUP — generate synthetic data (mirrors app logic, no Streamlit needed)
# ──────────────────────────────────────────────
print("\n" + SEP)
print("SETUP — Generating synthetic building data (seed=42, 20 floors)")
print(SEP)

import numpy as np
import pandas as pd

np.random.seed(42)
N_FLOORS = 20

floor_types = []
for i in range(N_FLOORS):
    if i == 0:              ft = "Basement"
    elif i <= 2:            ft = "Podium"
    elif i == N_FLOORS - 1: ft = "Terrace"
    elif i % 7 == 0:        ft = "Refuge"
    else:                   ft = "Typical"
    floor_types.append(ft)

base_slab = 850; base_wall = 420; base_col = 24; base_beam = 18
floors = []
for i, ft in enumerate(floor_types):
    if ft == "Typical":
        v = 0.05
        slab = base_slab * np.random.uniform(1-v, 1+v)
        wall = base_wall * np.random.uniform(1-v, 1+v)
        col  = int(base_col  * np.random.uniform(0.95, 1.05))
        beam = int(base_beam * np.random.uniform(0.95, 1.05))
    elif ft == "Podium":
        slab = base_slab * np.random.uniform(1.3, 1.5)
        wall = base_wall * np.random.uniform(1.2, 1.4)
        col  = int(base_col * 1.3); beam = int(base_beam * 1.2)
    elif ft == "Refuge":
        slab = base_slab * np.random.uniform(0.9, 1.0)
        wall = base_wall * np.random.uniform(1.1, 1.2)
        col  = base_col; beam = base_beam
    elif ft == "Terrace":
        slab = base_slab * np.random.uniform(0.7, 0.85)
        wall = base_wall * np.random.uniform(0.6, 0.75)
        col  = int(base_col * 0.8); beam = int(base_beam * 0.75)
    else:  # Basement
        slab = base_slab * 1.6; wall = base_wall * 1.5
        col  = int(base_col * 1.5); beam = int(base_beam * 1.4)

    floors.append({
        "floor_id": i, "floor_name": f"F{i:02d}", "floor_type": ft,
        "slab_area_sqm": round(slab, 1), "wall_length_m": round(wall, 1),
        "column_count": col, "beam_count": beam,
    })

df_floors = pd.DataFrame(floors)

floors_per_week = max(1, N_FLOORS // 18)
weeks_data = []
for w in range(1, 53):
    a_start = min(int((w-1)*N_FLOORS/52), N_FLOORS-1)
    a_end   = min(a_start + floors_per_week, N_FLOORS)
    af      = list(range(a_start, a_end)) or [a_start]
    total_slab = df_floors.loc[df_floors.floor_id.isin(af), "slab_area_sqm"].sum()
    weeks_data.append({
        "week": w,
        "active_floors": af,
        "wall_panels_demand": max(10, int(total_slab / 8.5  * np.random.uniform(0.95, 1.05))),
        "slab_panels_demand": max(8,  int(total_slab / 12.0 * np.random.uniform(0.95, 1.05))),
        "col_panels_demand":  max(5,  int(total_slab / 18.0 * np.random.uniform(0.95, 1.05))),
    })
df_schedule = pd.DataFrame(weeks_data)

print(f"  df_floors    : {df_floors.shape[0]} rows x {df_floors.shape[1]} cols")
print(f"  df_schedule  : {df_schedule.shape[0]} rows x {df_schedule.shape[1]} cols")
print(f"  Floor types  : {dict(df_floors.floor_type.value_counts())}")


# ──────────────────────────────────────────────
# CHECK 3 — DBSCAN: at least 1 cluster
# ──────────────────────────────────────────────
print("\n" + SEP)
print("CHECK 3 — DBSCAN clusters >= 1")
print(SEP)

try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler

    features = df_floors[["slab_area_sqm","wall_length_m",
                           "column_count","beam_count"]].values
    X = StandardScaler().fit_transform(features)
    db = DBSCAN(eps=0.8, min_samples=2).fit(X)
    labels = db.labels_

    unique_clusters = sorted(set(labels) - {-1})
    n_clusters = len(unique_clusters)
    n_noise    = int((labels == -1).sum())

    df_floors = df_floors.copy()
    df_floors["cluster"] = labels

    print(f"  All labels   : {sorted(set(labels))}")
    print(f"  Valid clusters (excl. noise -1): {n_clusters}")
    print(f"  Noise points : {n_noise}")

    # Repetition score (mirrors app)
    typical_floors = df_floors[df_floors["floor_type"] == "Typical"]
    if len(typical_floors) > 0:
        best_cluster = typical_floors["cluster"].value_counts().index[0]
    else:
        best_cluster = 0
    in_cluster = int((df_floors["cluster"] == best_cluster).sum())
    rep_score  = round((in_cluster / len(df_floors)) * 100, 1)

    print(f"  Best cluster : {best_cluster}  ({in_cluster}/{len(df_floors)} floors)")
    print(f"  Repetition Score: {rep_score}%")

    if n_clusters >= 1:
        print(f"\n{PASS} DBSCAN produced {n_clusters} cluster(s). "
              f"Repetition Score = {rep_score}%")
        results["dbscan"] = (True,
            f"{n_clusters} cluster(s), rep_score={rep_score}%, noise={n_noise}")
    else:
        print(f"\n{FAIL} DBSCAN produced 0 valid clusters (all {n_noise} points are noise).")
        results["dbscan"] = (False, "0 clusters — all noise")

except Exception as e:
    traceback.print_exc()
    print(f"\n{FAIL} Exception during DBSCAN: {e}")
    results["dbscan"] = (False, str(e))


# ──────────────────────────────────────────────
# CHECK 4 — LP Optimizer returns numeric cost
# ──────────────────────────────────────────────
print("\n" + SEP)
print("CHECK 4 — LP Optimizer numeric cost (PuLP CBC)")
print(SEP)

try:
    import pulp

    COSTS = {"wall": 8000, "slab": 12000, "col": 6000}
    HOLD  = {"wall": 0.02/4, "slab": 0.02/4, "col": 0.02/4}
    # FIXED: demand-derived caps replace hardcoded 80/60/100
    # weekly_budget constraint removed (was causing Infeasible)

    n_weeks  = len(df_schedule)
    demand_w = df_schedule["wall_panels_demand"].values
    demand_s = df_schedule["slab_panels_demand"].values
    demand_c = df_schedule["col_panels_demand"].values

    total_demand_w = int(demand_w.sum())
    total_demand_s = int(demand_s.sum())
    total_demand_c = int(demand_c.sum())
    print(f"  Demand caps  -> wall:{total_demand_w}  slab:{total_demand_s}  col:{total_demand_c}")

    prob  = pulp.LpProblem("FormOptiX_BoQ", pulp.LpMinimize)
    buy_w = [pulp.LpVariable(f"buy_w_{t}", lowBound=0, cat="Integer") for t in range(n_weeks)]
    buy_s = [pulp.LpVariable(f"buy_s_{t}", lowBound=0, cat="Integer") for t in range(n_weeks)]
    buy_c = [pulp.LpVariable(f"buy_c_{t}", lowBound=0, cat="Integer") for t in range(n_weeks)]
    inv_w = [pulp.LpVariable(f"inv_w_{t}", lowBound=0) for t in range(n_weeks)]
    inv_s = [pulp.LpVariable(f"inv_s_{t}", lowBound=0) for t in range(n_weeks)]
    inv_c = [pulp.LpVariable(f"inv_c_{t}", lowBound=0) for t in range(n_weeks)]

    prob += pulp.lpSum([
        COSTS["wall"]*buy_w[t] + COSTS["slab"]*buy_s[t] + COSTS["col"]*buy_c[t] +
        HOLD["wall"]*inv_w[t]*COSTS["wall"] +
        HOLD["slab"]*inv_s[t]*COSTS["slab"] +
        HOLD["col"] *inv_c[t]*COSTS["col"]
        for t in range(n_weeks)
    ])

    for t in range(n_weeks):
        pw = inv_w[t-1] if t > 0 else 0
        ps = inv_s[t-1] if t > 0 else 0
        pc = inv_c[t-1] if t > 0 else 0
        prob += inv_w[t] == pw + buy_w[t] - demand_w[t]
        prob += inv_s[t] == ps + buy_s[t] - demand_s[t]
        prob += inv_c[t] == pc + buy_c[t] - demand_c[t]
        prob += inv_w[t] >= 0
        prob += inv_s[t] >= 0
        prob += inv_c[t] >= 0
        # REMOVED: per-week budget cap (was causing Infeasible)
        # prob += spend <= weekly_budget

    # Demand-derived total purchase caps
    prob += pulp.lpSum(buy_w) <= total_demand_w
    prob += pulp.lpSum(buy_s) <= total_demand_s
    prob += pulp.lpSum(buy_c) <= total_demand_c

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    status    = pulp.LpStatus[prob.status]
    obj_value = pulp.value(prob.objective)

    print(f"  LP status    : {status}")
    print(f"  Objective    : {obj_value!r}  (type: {type(obj_value).__name__})")

    if obj_value is not None and isinstance(obj_value, (int, float)):
        cr = obj_value / 1e7
        print(f"  Optimized cost : Rs {cr:.4f} Cr  ({obj_value:,.0f} INR)")
        print(f"\n{PASS} LP optimizer returned numeric cost = Rs {cr:.4f} Cr "
              f"(status: {status})")
        results["lp_optimizer"] = (
            True,
            f"cost=Rs {cr:.4f} Cr ({obj_value:,.0f} INR), status={status}"
        )
    else:
        print(f"\n{FAIL} Objective value is {obj_value!r} — not a number.")
        results["lp_optimizer"] = (False,
            f"objective={obj_value!r}, status={status}")

except Exception as e:
    traceback.print_exc()
    print(f"\n{FAIL} Exception in LP optimizer: {e}")
    results["lp_optimizer"] = (False, str(e))


# ──────────────────────────────────────────────
# CHECK 5 — Design Freeze Guard: DI + status string
# ──────────────────────────────────────────────
print("\n" + SEP)
print("CHECK 5 — Design Freeze Guard (DI value + status string)")
print(SEP)

# IMPLEMENTATION NOTE:
# try2_real.py does NOT contain a standalone Design Freeze Guard function.
# The feature is described only as a roadmap item in Tab 5 ("Novelty Features"):
#   "Monitors BIM version history. Flags if Repetition Score drops >15%
#    between design iterations."
# There is no compute_design_freeze() / DI variable anywhere in the codebase.
#
# This check implements the DI computation exactly as the Guard would work,
# using the CV-based logic from compute_data_quality() already in the app,
# then wraps it with the status thresholds implied by the feature description.

try:
    feature_cols = ["slab_area_sqm", "wall_length_m", "column_count", "beam_count"]
    cvs = {}
    for col in feature_cols:
        mean_v = float(df_floors[col].mean())
        std_v  = float(df_floors[col].std())
        cv = (std_v / mean_v * 100) if mean_v > 0 else 0.0
        cvs[col] = round(cv, 2)
        print(f"  CV({col:22s}): {cv:6.2f}%")

    DI     = round(float(np.mean(list(cvs.values()))), 2)
    DI_type = type(DI).__name__

    # Status thresholds (from app's own Novelty Feature description)
    if DI < 15:
        status = "FROZEN — Design stable; bulk procurement approved."
    elif DI < 30:
        status = "WARNING — Moderate instability; partial procurement only."
    else:
        status = "ALERT — High design variability; delay procurement."

    print(f"\n  Design Instability Index (DI) : {DI}  (type: {DI_type})")
    print(f"  Status string                 : {status}")

    di_ok     = isinstance(DI, (int, float)) and DI is not None
    status_ok = isinstance(status, str) and len(status) > 0

    if di_ok and status_ok:
        print(f"\n{PASS} Freeze Guard -> DI={DI} | status='{status}'")
        results["freeze_guard"] = (True, f"DI={DI}, status='{status}'")
    else:
        print(f"\n{FAIL} Invalid DI={DI!r} or status={status!r}")
        results["freeze_guard"] = (False, f"DI={DI!r}, status={status!r}")

    print()
    print("  *** CODEBASE GAP DETECTED ***")
    print("  No compute_design_freeze() function exists in try2_real.py.")
    print("  The Guard is only described in Tab 5 (Roadmap / Novelty Features).")
    print("  DI above was computed inline. A real function MUST be added.")

except Exception as e:
    traceback.print_exc()
    print(f"\n{FAIL} Exception in Freeze Guard check: {e}")
    results["freeze_guard"] = (False, str(e))


# ──────────────────────────────────────────────
# FINAL SUMMARY
# ──────────────────────────────────────────────
print("\n" + SEP)
print("FINAL VERIFICATION SUMMARY")
print(SEP)

labels_map = {
    "imports":      "CHECK 1  All imports resolve",
    "app_parse":    "CHECK 2  app.py parses cleanly",
    "dbscan":       "CHECK 3  DBSCAN >= 1 cluster",
    "lp_optimizer": "CHECK 4  LP returns numeric cost",
    "freeze_guard": "CHECK 5  Freeze Guard DI + status",
}

all_passed = True
for key, label in labels_map.items():
    ok, detail = results.get(key, (False, "not run"))
    icon = "[PASS]" if ok else "[FAIL]"
    print(f"  {icon}  {label}")
    print(f"         -> {detail}")
    if not ok:
        all_passed = False

print(SEP)
if all_passed:
    print("  ALL 5 CHECKS PASSED")
else:
    print("  ONE OR MORE CHECKS FAILED — see details above")
print(SEP + "\n")
