import sys
sys.path.insert(0, ".")
from utils.demand_calc import compute_is456_strip_weeks, build_reuse_matrix
import pandas as pd

checks = []

# 1. All 5 new columns, correct types
test_df = pd.DataFrame([
    {"floor_id": 1, "week_start": 2, "week_end": 4, "strip_week": 6},
    {"floor_id": 2, "week_start": 5, "week_end": 7, "strip_week": 3},   # violation
    {"floor_id": 3, "week_start": 8, "week_end": 10, "strip_week": 10},
])
result = compute_is456_strip_weeks(test_df)
required = {
    "strip_week_wall", "strip_week_slab", "strip_week_cantilever",
    "strip_week_user", "effective_strip_week", "is456_violation"
}
checks.append(("All 5 new columns present",           required.issubset(set(result.columns))))
checks.append(("is456_violation is boolean",           result["is456_violation"].dtype == bool))
checks.append(("Violation detected for floor 2",       bool(result.loc[result.floor_id == 2, "is456_violation"].iloc[0])))
checks.append(("No violation for floor 1",             not bool(result.loc[result.floor_id == 1, "is456_violation"].iloc[0])))

# 2. effective_strip_week = max(user, slab) for user>0
for _, row in result.iterrows():
    exp = max(int(row["strip_week_user"]), int(row["strip_week_slab"])) if row["strip_week_user"] > 0 else int(row["strip_week_slab"])
    checks.append((f"effective_strip_week floor {int(row.floor_id)}", int(row["effective_strip_week"]) == exp))

# 3. Missing strip_week auto-generated
df2 = pd.DataFrame([
    {"floor_id": 1, "week_start": 2, "week_end": 5},
    {"floor_id": 2, "week_start": 6, "week_end": 9},
])
r2 = compute_is456_strip_weeks(df2)
checks.append(("No KeyError if strip_week missing",   "effective_strip_week" in r2.columns))
checks.append(("Auto strip_week = week_end+2",        bool((r2["strip_week_user"] == r2["week_end"] + 2).all())))

# 4. build_reuse_matrix uses effective_strip_week
matrix = build_reuse_matrix(result, transport_weeks=1)
checks.append(("build_reuse_matrix accepted df",      matrix is not None and len(matrix) > 0))

# 5. Demo data: effective = max(user, week_start+2) for all
demo_df = pd.DataFrame([
    {"floor_id": i, "week_start": i * 2, "week_end": i * 2 + 1, "strip_week": i * 2 + 4}
    for i in range(1, 6)
])
demo_r = compute_is456_strip_weeks(demo_df)
ok_demo = all(
    int(r["effective_strip_week"]) == max(int(r["strip_week_user"]), int(r["strip_week_slab"]))
    for _, r in demo_r.iterrows()
)
checks.append(("Demo data effective = max(user, week_start+2)", ok_demo))

# 6. Source file checks
src = open("try2_real.py", encoding="utf-8").read()
pdf = open("utils/report_generator.py", encoding="utf-8").read()
dc  = open("utils/demand_calc.py",      encoding="utf-8").read()

checks.append(("import in try2_real",                 "compute_is456_strip_weeks" in src))
checks.append(("Called before clustering",            "df_floors = compute_is456_strip_weeks(df_floors)" in src))
checks.append(("IS 456 expander present",             "IS 456 Stripping Schedule" in src))
checks.append(("Violation warning conditional",       "_viols > 0" in src))
checks.append(("Caption in Tab 1",                    "IS\u00a0456:2000, Clause\u00a011.3, Table\u00a011" in src))
checks.append(("PDF Page 3 new column header",        "IS 456 strip (wk)" in pdf))
checks.append(("PDF effective_strip_week .get",       'row.get("effective_strip_week"' in pdf))
checks.append(("Academic comment in demand_calc",     "IS 456:2000, Clause 11.3, Table 11" in dc))
checks.append(("matrix picks effective col",          '"effective_strip_week" if "effective_strip_week" in df.columns' in dc))

# Print
print("=" * 68)
print("IS 456 Stripping Schedule — Step 6 Checklist")
print("=" * 68)
all_pass = True
for label, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'} | {label}")
    if not ok:
        all_pass = False
print()
print("All checks passed!" if all_pass else "One or more checks FAILED.")
