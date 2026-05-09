"""
Verify predict_design_change_risk() -- Step 5 checklist.
Run from the try1/ directory.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from freeze_guard import predict_design_change_risk

checks = []

# ── 1. Empty history → no crash, INSUFFICIENT DATA ────────────────────
r = predict_design_change_risk([])
checks.append(("Empty list → no crash", True))  # reaching here = passed
checks.append(("Empty list → INSUFFICIENT DATA", r["risk_level"] == "INSUFFICIENT DATA"))
checks.append(("Empty list → total_count = 0", r["total_count"] == 0))
checks.append(("Empty list → trend = 0.0", r["trend"] == 0.0))

# ── 2. Single entry → INSUFFICIENT DATA ────────────────────────────────
r1 = predict_design_change_risk([12.5])
checks.append(("len=1 → INSUFFICIENT DATA", r1["risk_level"] == "INSUFFICIENT DATA"))
checks.append(("len=1 → trend = 0.0 (no crash)", r1["trend"] == 0.0))

# ── 3. di_history cap at 5 verified via try2_real.py source ───────────
src = open("try2_real.py", encoding="utf-8").read()
checks.append(("di_history capped at 5", '[-5:]' in src))
checks.append(("di_history initialized if absent", '"di_history" not in st.session_state' in src))
checks.append(("di_history.append called", 'st.session_state["di_history"].append' in src))

# ── 4. HIGH requires BOTH above_threshold_count >= 2 AND trend > 0 ────
# Case: 2 above threshold but trend <= 0 → should NOT be HIGH
r_not_high = predict_design_change_risk([15.0, 11.0])  # above_count=2, trend=-4
checks.append(("Trending DOWN with 2 above → NOT HIGH",
               r_not_high["risk_level"] != "HIGH"))

# Case: trend > 0 but only 1 above threshold → NOT HIGH
r_not_high2 = predict_design_change_risk([5.0, 11.0])  # above_count=1, trend=+6
checks.append(("Only 1 above threshold → NOT HIGH",
               r_not_high2["risk_level"] != "HIGH"))

# Case: BOTH conditions → HIGH
r_high = predict_design_change_risk([11.0, 8.0, 13.0])  # above_count=2, trend=+2
checks.append(("Both conditions met → HIGH", r_high["risk_level"] == "HIGH"))

# ── 5. MEDIUM cases ────────────────────────────────────────────────────
r_med1 = predict_design_change_risk([5.0, 11.0])   # above_count=1
checks.append(("1 above threshold → at least MEDIUM", r_med1["risk_level"] == "MEDIUM"))

r_med2 = predict_design_change_risk([3.0, 9.0])    # trend=+6 > 5, no above
checks.append(("trend > 5 (no above) → MEDIUM", r_med2["risk_level"] == "MEDIUM"))

# ── 6. LOW case ────────────────────────────────────────────────────────
r_low = predict_design_change_risk([5.0, 7.0])   # above_count=0, trend=+2
checks.append(("No breach, small trend → LOW", r_low["risk_level"] == "LOW"))

# ── 7. Confidence levels ───────────────────────────────────────────────
r_c2 = predict_design_change_risk([5.0, 7.0])
r_c3 = predict_design_change_risk([5.0, 7.0, 9.0])
checks.append(("len=2 → confidence moderate", r_c2["confidence"] == "moderate"))
checks.append(("len=3 → confidence high",     r_c3["confidence"] == "high"))

# ── 8. Citation present in function output ────────────────────────────
checks.append(("Citation in output", "Ibbs" in r_high["citation"]))

# ── 9. Sparkline only renders when len >= 2 ───────────────────────────
checks.append(("Sparkline gated on len >= 2",
               'if len(_di_history) >= 2:' in src))

# ── 10. Citation in UI caption ────────────────────────────────────────
checks.append(("Ibbs citation in UI caption",
               "Ibbs (1997)" in src and "3\\u00d7 higher" in src))

# ── 11. Fresh first upload → INSUFFICIENT DATA shown ─────────────────
r_first = predict_design_change_risk([8.5])
checks.append(("First upload (len=1) → INSUFFICIENT DATA",
               r_first["risk_level"] == "INSUFFICIENT DATA"))

# ── 12. Second upload with DI > 10 both times → at least MEDIUM ──────
r_second = predict_design_change_risk([12.0, 11.5])  # both > 10, trend=-0.5
# above_count=2, trend=-0.5 → NOT HIGH (no upward trend), but above_count>=2 → MEDIUM
checks.append(("Two DI>10 readings → at least MEDIUM",
               r_second["risk_level"] in ("MEDIUM", "HIGH")))

# ── 13. predict_design_change_risk in import ──────────────────────────
checks.append(("predict_design_change_risk imported in try2_real",
               "predict_design_change_risk" in src))

# ── Print results ─────────────────────────────────────────────────────
print("=" * 65)
print("Design Change Trend Prediction — Checklist")
print("=" * 65)
all_pass = True
for label, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'} | {label}")
    if not ok:
        all_pass = False
print()
print("All checks passed!" if all_pass else "One or more checks FAILED.")
