"""
Verify compute_sensitivity_table() and Tab 2 expander — Step 3 checklist.
Tests the function logic directly (no try2_real import to avoid Streamlit top-level code).
Run from try1/ directory.
"""
import sys, importlib, types
sys.stdout.reconfigure(encoding="utf-8")

# ── Extract function without importing the full Streamlit app ─────────────
# Read source, exec only the function definition
src = open("try2_real.py", encoding="utf-8").read()

# Find function block
start = src.index("def compute_sensitivity_table(")
# Find the next top-level def or class after the function
import re
nxt = re.search(r"\n(?:def |class |\# =)", src[start + 10:])
end = start + 10 + nxt.start() if nxt else len(src)
func_src = src[start:end]

_ns = {}
exec(func_src, _ns)
compute_sensitivity_table = _ns["compute_sensitivity_table"]

checks = []

# 1. Guard: base_baseline = 0 returns [] (no /0 crash)
r0 = compute_sensitivity_table(100_000, 0, 15.0)
checks.append(("base_baseline=0 returns [] (no crash)", r0 == []))

# 2. Returns 7 rows for normal input
BASE_OPT  = 14_910_000.0
BASE_BASE = 17_610_000.0
BASE_PCT  = 15.3
rows = compute_sensitivity_table(BASE_OPT, BASE_BASE, BASE_PCT)
checks.append(("Returns 7 rows", len(rows) == 7))

# 3. adj_savings_pct floored at 0 for all rows
for r in rows:
    checks.append((f"  '{r['scenario']}' pct >= 0", r["adj_savings_pct"] >= 0.0))

# 4. adj_savings (Cr) floored at 0 for all rows
for r in rows:
    checks.append((f"  '{r['scenario']}' savings_cr >= 0", r["adj_savings"] >= 0.0))

# 5. Base case is first row
checks.append(("First row is Base case", rows[0]["scenario"] == "Base case"))

# 6. Panel cost +50%: both baseline and optimized scale by 1.5
r_plus = next(r for r in rows if r["scenario"] == "Panel cost +50%")
expected_base = round(BASE_BASE * 1.5 / 1e7, 2)
expected_opt  = round(BASE_OPT  * 1.5 / 1e7, 2)
checks.append(("Panel+50% baseline = base * 1.5",
               abs(r_plus["adj_baseline"] - expected_base) < 0.01))
checks.append(("Panel+50% optimized = opt * 1.5",
               abs(r_plus["adj_optimized"] - expected_opt) < 0.01))

# 7. Operational scenario (Schedule): only optimized changes, baseline unchanged
r_sched = next(r for r in rows if "Schedule" in r["scenario"])
checks.append(("Schedule: baseline unchanged",
               abs(r_sched["adj_baseline"] - round(BASE_BASE / 1e7, 2)) < 0.01))
checks.append(("Schedule: optimized = opt * 1.08",
               abs(r_sched["adj_optimized"] - round(BASE_OPT * 1.08 / 1e7, 2)) < 0.01))

# 8. Optimistic reuse: optimized decreases 10%
r_opt = next(r for r in rows if "Optimistic" in r["scenario"])
checks.append(("Optimistic reuse: optimized = opt * 0.90",
               abs(r_opt["adj_optimized"] - round(BASE_OPT * 0.90 / 1e7, 2)) < 0.01))

# 9. Savings % rounded to 1dp for all rows
for r in rows:
    checks.append((f"  '{r['scenario']}' pct is 1dp",
                   r["adj_savings_pct"] == round(r["adj_savings_pct"], 1)))

# 10. Savings Cr rounded to 2dp for all rows
for r in rows:
    for key in ("adj_baseline", "adj_optimized", "adj_savings"):
        checks.append((f"  '{r['scenario']}' {key} is 2dp",
                       r[key] == round(r[key], 2)))

# 11. Best/worst computable and sensible
best  = max(r["adj_savings_pct"] for r in rows)
worst = min(r["adj_savings_pct"] for r in rows)
checks.append(("best > 0", best > 0))
checks.append(("worst >= 0", worst >= 0))
checks.append(("best >= worst", best >= worst))

# 12. Source-level UI requirements
checks.append(("st.expander collapsed by default",
               'expanded=False' in src and 'Savings sensitivity' in src))
checks.append(("st.dataframe used (not st.table)",
               'st.dataframe(_styled_sens' in src))
checks.append(("Best case savings metric",   '"Best case savings"' in src))
checks.append(("Worst case savings metric",  '"Worst case savings"' in src))
checks.append(("Savings range metric",       '"Savings range"' in src))
checks.append(("Hillier & Lieberman citation",
               'Hillier & Lieberman (2021)' in src))
checks.append(("Dynamic range in caption (_worst_pct/_best_pct)",
               '_worst_pct:.1f' in src and '_best_pct:.1f' in src))
checks.append(("Phase 2 note in caption",    'Phase 2' in src))
checks.append(("what-if slider help= restored",
               'Ibbs, 1997: scope change impact on procurement' in src))
checks.append(("Sensitivity expander before BoQ table in source",
               src.index('Savings sensitivity') < src.index('SKU-Level BoQ')))
checks.append(("_highlight_sens function defined",
               'def _highlight_sens' in src))
checks.append(("compute_sensitivity_table defined in try2_real",
               'def compute_sensitivity_table(' in src))

# ── Print results ─────────────────────────────────────────────────────────
print("=" * 68)
print("Sensitivity Analysis Feature -- Checklist")
print("=" * 68)
all_pass = True
for label, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'} | {label}")
    if not ok:
        all_pass = False
print()
print("All checks passed!" if all_pass else "One or more checks FAILED.")
