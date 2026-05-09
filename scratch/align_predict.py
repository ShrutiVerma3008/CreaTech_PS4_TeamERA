"""
Align freeze_guard.py and try2_real.py to the spec exactly.
Run from try1/ directory.
"""
import sys, re
sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 1. freeze_guard.py — replace the entire predict_design_change_risk function
# ─────────────────────────────────────────────────────────────────────────────
FG_PATH = r"d:\sem_6\creaTech\try1\freeze_guard.py"
with open(FG_PATH, encoding="utf-8") as f:
    fg = f.read()

# Find start and end of the function (ends where _run_tests begins)
fn_start = fg.index("def predict_design_change_risk(")
fn_end   = fg.index("\n# ============================================================\n"
                    "# STEP 4")

NEW_FN = '''def predict_design_change_risk(di_history: list) -> dict:
    """
    Parameters
    ----------
    di_history : list of float
        DI values from successive uploads, most recent LAST.
        Length 0-5. Values are percentages (e.g. 12.5 not 0.125).

    Returns
    -------
    dict with keys:
        risk_level   : str  "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT DATA"
        confidence   : str  "high" (len>=3) | "moderate" (len==2) | "low" (len<=1)
        trend        : float  di_history[-1] - di_history[0], 0.0 if len < 2
        above_count  : int  count of values > 10.0
        total_count  : int  len(di_history)
        message      : str  (see logic below)
        citation     : str  always = canonical Ibbs 1997 string

    Academic basis
    --------------
    Ibbs, C.W. (1997). Quantitative impacts of project change.
    Journal of Construction Engineering and Management, 123(3), 308-311.
    Sustained DI exceedance above 10% across multiple measurement
    periods correlates with 3x higher late-stage design change probability.
    """
    _CITATION = (
        "Ibbs (1997) J.Const.Eng.Mgmt. 123(3) \u2014 "
        "sustained DI exceedance correlates with "
        "3x late-stage change probability"
    )

    # \u2500\u2500 Guard: empty list \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    if not di_history:
        return {
            "risk_level":  "INSUFFICIENT DATA",
            "confidence":  "low",
            "trend":       0.0,
            "above_count": 0,
            "total_count": 0,
            "message":     (
                "Upload more floor data across multiple sessions "
                "to enable trend-based prediction."
            ),
            "citation": _CITATION,
        }

    total = len(di_history)
    above = sum(1 for v in di_history if v > 10.0)
    trend = round(di_history[-1] - di_history[0], 2) if total >= 2 else 0.0
    conf  = "high" if total >= 3 else ("moderate" if total == 2 else "low")

    # \u2500\u2500 Guard: single value \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    if total <= 1:
        return {
            "risk_level":  "INSUFFICIENT DATA",
            "confidence":  "low",
            "trend":       0.0,
            "above_count": above,
            "total_count": total,
            "message":     (
                "Upload more floor data across multiple sessions "
                "to enable trend-based prediction."
            ),
            "citation": _CITATION,
        }

    # \u2500\u2500 Risk classification (Ibbs 1997 sustained-breach logic) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    # HIGH requires BOTH conditions \u2014 a single spike is not predictive.
    if above >= 2 and trend > 0:
        risk = "HIGH"
        msg  = (
            f"Design change probability HIGH. DI exceeded procurement "
            f"risk threshold in {above} of {total} measurements and "
            f"is trending upward (+{trend:.1f}pp). Defer procurement "
            f"of unstable clusters. (Ibbs 1997)"
        )
    elif above >= 1 or trend > 5.0:
        risk = "MEDIUM"
        msg  = (
            "Design change probability MEDIUM. Monitor closely. "
            "Procurement of stable clusters may proceed."
        )
    else:
        risk = "LOW"
        msg  = (
            "Design change probability LOW. Design appears stable. "
            "Full procurement recommended."
        )

    return {
        "risk_level":  risk,
        "confidence":  conf,
        "trend":       trend,
        "above_count": above,
        "total_count": total,
        "message":     msg,
        "citation":    _CITATION,
    }

'''

fg_new = fg[:fn_start] + NEW_FN + fg[fn_end:]
with open(FG_PATH, "w", encoding="utf-8") as f:
    f.write(fg_new)
print("freeze_guard.py updated")

# ─────────────────────────────────────────────────────────────────────────────
# 2. try2_real.py — replace the prediction UI block
# ─────────────────────────────────────────────────────────────────────────────
TR_PATH = r"d:\sem_6\creaTech\try1\try2_real.py"
with open(TR_PATH, encoding="utf-8") as f:
    tr = f.read()

# Find start and end of the old UI block
UI_START = "        # \u2500\u2500 Step 3: Design change trend prediction"
UI_END   = "            st.caption(\"DI history (last 5 uploads). Yellow line = 10% risk threshold.\")"

si = tr.index(UI_START)
ei = tr.index(UI_END) + len(UI_END)

NEW_UI = """        # \u2500\u2500 DI Trend Prediction \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        st.subheader("Design change trend prediction")
        _di_hist = st.session_state.get("di_history", [])
        _pred = predict_design_change_risk(_di_hist)

        _RISK_FN = {
            "HIGH":              st.error,
            "MEDIUM":            st.warning,
            "LOW":               st.success,
            "INSUFFICIENT DATA": st.info,
        }
        _RISK_FN.get(_pred["risk_level"], st.info)(_pred["message"])

        _pc1, _pc2, _pc3 = st.columns(3)
        _trend_str = (
            f"+{_pred['trend']:.1f}pp" if _pred["trend"] > 0
            else f"{_pred['trend']:.1f}pp"
        )
        _pc1.metric("DI trend",
                    _trend_str,
                    help="Change in DI from first to latest upload")
        _pc2.metric("Measurements above 10% threshold",
                    f"{_pred['above_count']} / {_pred['total_count']}")
        _pc3.metric("Prediction confidence", _pred["confidence"].title())

        if len(_di_hist) >= 2:
            import pandas as _pd_pred
            _hist_df = _pd_pred.DataFrame({
                "DI (%)":         _di_hist,
                "Risk threshold": [10.0] * len(_di_hist),
            })
            st.line_chart(_hist_df)
            st.caption(
                "DI history across uploads. Risk threshold = 10% "
                "(Ibbs 1997 \u2014 procurement risk inflection point)."
            )

        st.caption(_pred["citation"])"""

tr_new = tr[:si] + NEW_UI + tr[ei:]
with open(TR_PATH, "w", encoding="utf-8") as f:
    f.write(tr_new)
print("try2_real.py updated")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Syntax check both files
# ─────────────────────────────────────────────────────────────────────────────
import ast
for path, label in [(FG_PATH, "freeze_guard.py"), (TR_PATH, "try2_real.py")]:
    try:
        ast.parse(open(path, encoding="utf-8").read())
        print(f"Syntax OK: {label}")
    except SyntaxError as e:
        print(f"SYNTAX ERROR in {label}: {e}")
        sys.exit(1)
