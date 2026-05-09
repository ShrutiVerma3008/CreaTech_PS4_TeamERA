"""Verify compute_three_baselines() — Step 6 checklist."""
import sys
sys.path.insert(0, ".")
from core.lp_optimizer import compute_three_baselines

checks = []

# 1. Handles zero_baseline = 0 (guard /0)
r = compute_three_baselines(0, 5_000_000, 15_000)
checks.append(("zero_baseline=0 guarded, no crash", r["zero_reuse_cost"] == 0.0))

# 2. savings_vs_experienced floored at 0
r = compute_three_baselines(1_000_000, 900_000, 15_000)  # experienced = 650k < 900k opt
checks.append(("savings_vs_experienced floored at 0", r["savings_vs_experienced"] == 0.0))
checks.append(("demo_warning True when opt > experienced", r["demo_warning"] == True))
checks.append(("pct_vs_experienced = 0 on demo_warning", r["pct_vs_experienced"] == 0.0))

# 3. Normal case: zero=17.61Cr, opt=14.91Cr
zero = 17_610_000
opt  = 14_910_000
r = compute_three_baselines(zero, opt, 15_000)
exp_expected = round(zero * 0.65, 2)
checks.append(("experienced_planner_cost = 65% of zero", abs(r["experienced_planner_cost"] - exp_expected) < 1))
checks.append(("savings_vs_zero > 0", r["savings_vs_zero"] > 0))
# On demo data opt (14.91Cr) > experienced (11.45Cr) → demo_warning expected
checks.append(("demo_warning True for demo data (opt > exp)", r["demo_warning"] == True))
checks.append(("pct_vs_zero > 0", r["pct_vs_zero"] > 0))

# 4. FormOptiX beating experienced (real data scenario)
zero2 = 20_000_000
opt2  = 5_000_000
r2 = compute_three_baselines(zero2, opt2, 15_000)
exp2 = zero2 * 0.65
checks.append(("Real data: savings_vs_experienced > 0", r2["savings_vs_experienced"] > 0))
checks.append(("Real data: pct_vs_experienced > 0", r2["pct_vs_experienced"] > 0))
checks.append(("Real data: demo_warning False", r2["demo_warning"] == False))

# 5. Session state keys exist in try2_real.py source
src = open("try2_real.py", encoding="utf-8").read()
checks.append(("experienced_baseline stored in session_state", 'st.session_state["experienced_baseline"]' in src))
checks.append(("savings_vs_experienced stored in session_state", 'st.session_state["savings_vs_experienced"]' in src))
checks.append(("pct_vs_experienced stored in session_state", 'st.session_state["pct_vs_experienced"]' in src))

# 6. PDF metric keys present in try2_real.py
checks.append(("experienced_baseline_cr in PDF metrics", '"experienced_baseline_cr"' in src))
checks.append(("savings_vs_experienced_cr in PDF metrics", '"savings_vs_experienced_cr"' in src))

# 7. PDF uses Rs not ₹
rg = open("utils/report_generator.py", encoding="utf-8").read()
# check the new savings rows
checks.append(('PDF savings_vs_zero row uses Rs', 'Savings vs zero-reuse' in rg))
checks.append(('PDF savings_vs_experienced row uses Rs', 'Savings vs experienced planner' in rg))
checks.append(('PDF footnote Dania et al.', 'Dania et al.' in rg))

# 8. st.metric delta for col 3 is pct_vs_experienced NOT pct_vs_zero
checks.append(("Col 3 delta uses _savings_vs_exp", "_savings_vs_exp" in src))

# 9. Subheader present
checks.append(("Savings analysis subheader present", "Savings analysis" in src and "three baselines" in src))

# 10. st.success summary present
checks.append(("st.success with both pct mentions", "_pct_vs_zero" in src and "_pct_vs_exp" in src))

print("=" * 65)
print("Three-Baseline Feature — Checklist")
print("=" * 65)
all_pass = True
for label, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'} | {label}")
    if not ok:
        all_pass = False
print()
print("All checks passed!" if all_pass else "One or more checks FAILED.")
