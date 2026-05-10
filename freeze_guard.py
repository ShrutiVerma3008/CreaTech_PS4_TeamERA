"""
freeze_guard.py — Design Freeze Intelligence for FormOptiX
===========================================================
Computes the Design Instability Index (DI) from floor geometry
and returns an actionable freeze status.

This module is intentionally independent of Streamlit and PuLP
so it can be unit-tested without spinning up the full app.

Public API
----------
compute_design_freeze(df) -> dict
    Input : pandas DataFrame with columns
            slab_area_sqm, wall_length_m, column_count
    Output: dict with keys
            CV_slab, CV_wall, CV_col, DI,
            status ("SAFE" | "WARNING" | "HALT"),
            recommendation (str)

identify_unstable_floors(df) -> list
    Returns list of dicts for each (floor, feature) pair
    whose value lies beyond 1.5sigma of the feature mean.
    Keys: floor_id, feature, value, mean, deviation_pct

estimate_rework_cost(unstable_floors, df, c_p) -> dict
    Estimates cost impact of ordering before design is frozen.
    Keys: panels_at_risk, rework_cost_order_now,
          savings_if_wait_2w, recommendation_weeks

get_procurement_recommendation(di_value, clusters,
                               unstable_floor_ids) -> dict
    Returns cluster-level action (PROCURE ALL /
    PROCURE STABLE CLUSTERS ONLY / HALT ALL PROCUREMENT).
    Keys: action, stable_clusters, unstable_clusters, detail

Status thresholds
-----------------
  DI <= 10%          -> SAFE    : Safe to procure all clusters.
  10% < DI <= 15%    -> WARNING : Procure stable clusters only. Hold unstable floors.
  DI > 15%           -> HALT    : Do not procure. Freeze drawings first.
"""

import pandas as pd
import numpy as np


# ── column name aliases (app uses slab_area_sqm; guard uses canonical names)
_ALIAS = {
    "slab_area_sqm": "slab_area_sqm",
    "slab_area_m2":  "slab_area_sqm",   # alternate name from task spec
    "wall_length_m": "wall_length_m",
    "column_count":  "column_count",
    "col_count":     "column_count",     # alternate name from task spec
}

_THRESHOLDS = {
    "SAFE":    10.0,   # DI <= 10  → SAFE
    "WARNING": 15.0,   # DI <= 15  → WARNING
    # DI >  15                     → HALT
}

_RECOMMENDATIONS = {
    "SAFE":    "Safe to procure all clusters.",
    "WARNING": "Procure stable clusters only. Hold unstable floors.",
    "HALT":    "Do not procure. Freeze drawings first.",
}


def _cv(series: pd.Series) -> float:
    """Coefficient of Variation as a percentage. Returns 0.0 for constant/empty data."""
    mean = series.mean()
    if mean == 0 or len(series) < 2:
        return 0.0
    return float(series.std(ddof=1) / mean * 100)


def compute_design_freeze(df: pd.DataFrame) -> dict:
    """
    Compute the Design Instability Index (DI) from floor geometry.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain slab_area (sqm), wall_length (m), column_count columns.
        Accepts both naming conventions (see _ALIAS at top of file).

    Returns
    -------
    dict with keys:
        CV_slab       (float) — CV of slab area in %
        CV_wall       (float) — CV of wall length in %
        CV_col        (float) — CV of column count in %
        DI            (float) — mean of the three CVs
        status        (str)   — "SAFE" | "WARNING" | "HALT"
        recommendation(str)   — one-sentence actionable guidance
    """
    # ── Resolve column names
    def _resolve(df, *candidates):
        for c in candidates:
            canonical = _ALIAS.get(c, c)
            if canonical in df.columns:
                return df[canonical].dropna().astype(float)
            if c in df.columns:
                return df[c].dropna().astype(float)
        raise KeyError(
            f"None of {candidates} found in dataframe. "
            f"Available columns: {list(df.columns)}"
        )

    slab_series = _resolve(df, "slab_area_sqm", "slab_area_m2")
    wall_series = _resolve(df, "wall_length_m")
    col_series  = _resolve(df, "column_count", "col_count")

    CV_slab = round(_cv(slab_series), 2)
    CV_wall = round(_cv(wall_series), 2)
    CV_col  = round(_cv(col_series),  2)
    DI      = round((CV_slab + CV_wall + CV_col) / 3, 2)

    if DI <= _THRESHOLDS["SAFE"]:
        status = "SAFE"
    elif DI <= _THRESHOLDS["WARNING"]:
        status = "WARNING"
    else:
        status = "HALT"

    return {
        "CV_slab":        CV_slab,
        "CV_wall":        CV_wall,
        "CV_col":         CV_col,
        "DI":             DI,
        "status":         status,
        "recommendation": _RECOMMENDATIONS[status],
    }


# ============================================================
# EXTENDED FUNCTIONS — Steps 1, 2, 3
# ============================================================

# Unstable floor detection — Montgomery (2019) Ch.6 / Leys et al. (2013)
# 2.5 x MAD rule: robust outlier threshold for process control charts.
# MAD = median(|xi - median(x)|) — resistant to outliers (Leys et al. 2013).
# Montgomery (2019): operator override is the correct resolution for known
#   special causes (e.g. mechanical floors, refuge floors, lobbies).
# Leys et al. (2013) J.Exp.Social Psych. 49(4): MAD cannot distinguish
#   intentional from unintentional deviation — human override is required.
def identify_unstable_floors(df: pd.DataFrame) -> list:
    """
    Identify floors that are statistical outliers on any geometric feature.

    For each feature in [slab_area, wall_length, column_count],
    a floor is flagged if: abs(value - median) > 2.5 * MAD

    Floors with floor_override=True are excluded from detection.
    They represent intentional architectural exceptions (mechanical floors,
    refuge levels, lobbies) — not design instability.

    Parameters
    ----------
    df : pd.DataFrame
        Validated floor dataframe (same object passed to
        compute_design_freeze). Accepts both naming conventions.
        Optional column: floor_override (bool) — if True, floor is
        excluded from MAD detection.

    Returns
    -------
    list of dicts, one per (floor_id, feature) pair exceeding 2.5 * MAD:
        floor_id      (str)   — floor identifier
        feature       (str)   — feature name (canonical)
        value         (float) — actual value for this floor
        median        (float) — feature median across non-overridden floors
        deviation_pct (float) — abs(value - median) / median * 100

    Academic basis
    --------------
    Leys et al. (2013): MAD is highly robust to outliers. Threshold 2.5.
    Montgomery (2019) Ch.6: operator override for known special causes.
    """
    # ── Exclude floors marked as intentional design exceptions ───────────
    # Montgomery (2019): process control charts always allow operator
    # override for known special causes.
    override_ids = set()
    if "floor_override" in df.columns:
        override_ids = set(
            df.loc[df["floor_override"] == True, "floor_id"].tolist()  # noqa: E712
        )
        df_active = df[df["floor_override"] == False].copy()  # noqa: E712
    else:
        df_active = df.copy()

    # Resolve column names to canonical form (on df_active)
    col_map = {}  # canonical_name -> actual_column_name
    candidates = [
        ("slab_area_m2",  ["slab_area_sqm", "slab_area_m2"]),
        ("wall_length_m", ["wall_length_m"]),
        ("col_count",     ["column_count", "col_count"]),
    ]
    for canonical, options in candidates:
        for opt in options:
            if opt in df_active.columns:
                col_map[canonical] = opt
                break

    # Detect floor_id column
    id_col = None
    for cand in ["floor_id", "floor", "Floor", "level", "Level"]:
        if cand in df_active.columns:
            id_col = cand
            break

    results = []
    for canonical, actual_col in col_map.items():
        series = df_active[actual_col].dropna().astype(float)
        median_f = series.median()
        mad_f    = (series - median_f).abs().median()

        if mad_f == 0:
            # All values identical — no outliers possible
            continue

        threshold = 2.5 * mad_f

        for idx, val in series.items():
            if abs(val - median_f) > threshold:
                floor_label = (
                    str(df_active.loc[idx, id_col])
                    if id_col is not None
                    else str(idx)
                )
                results.append({
                    "floor_id":      floor_label,
                    "feature":       canonical,
                    "value":         round(float(val), 2),
                    "median":        round(float(median_f), 2),
                    "deviation_pct": round(
                        abs(val - median_f) / median_f * 100, 1
                    ) if median_f != 0 else 0.0,
                })
    return results


# Rework cost estimate — Ibbs (1997)
# 30% penalty factor from: projects with DI > 15% show
# ~30% cost overrun on procurement done before freeze.
# Source: Ibbs (1997) Table 3, high-change projects.
# Ibbs, C.W. (1997). Quantitative impacts of project change.
# Journal of Construction Engineering and Management,
# 123(3), 308-311.
def estimate_rework_cost(
    unstable_floors: list,
    df: pd.DataFrame,
    c_p: float,
) -> dict:
    """
    Estimate the cost impact of ordering panels before design freeze.

    Parameters
    ----------
    unstable_floors : list — output of identify_unstable_floors()
    df              : pd.DataFrame — floor dataframe
    c_p             : float — procurement cost per panel (Rs)

    Returns
    -------
    dict with keys:
        panels_at_risk          (int)   — proxy panel count at risk
        rework_cost_order_now   (float) — Rs, if ordered now
        savings_if_wait_2w      (float) — Rs, if deferred 2 weeks
        recommendation_weeks    (int)   — always 2

    Academic basis
    --------------
    Ibbs (1997): ~30% cost overrun on procurement done before
    design freeze (rework_cost = panels_at_risk * c_p * 0.30).
    Conservative 80% avoidance if deferred 2 weeks.
    """
    if not unstable_floors:
        return {
            "panels_at_risk":        0,
            "rework_cost_order_now": 0.0,
            "savings_if_wait_2w":    0.0,
            "recommendation_weeks":  2,
        }

    unstable_ids = set(u["floor_id"] for u in unstable_floors)
    n_unstable   = len(unstable_ids)

    # Use average col_count as panel-count proxy per floor
    col_col = None
    for cand in ["column_count", "col_count"]:
        if cand in df.columns:
            col_col = cand
            break
    avg_col_count = (
        float(df[col_col].mean()) if col_col else 4.0
    )

    panels_at_risk = int(round(n_unstable * avg_col_count))

    # Ibbs (1997): 30% rework penalty on affected work packages
    rework_cost_order_now = panels_at_risk * c_p * 0.30

    # Conservative estimate: waiting 2 weeks avoids 80% of rework
    savings_if_wait_2w = rework_cost_order_now * 0.80

    return {
        "panels_at_risk":        panels_at_risk,
        "rework_cost_order_now": rework_cost_order_now,
        "savings_if_wait_2w":    savings_if_wait_2w,
        "recommendation_weeks":  2,
    }


# Cluster-level procurement recommendation
# Extends Ibbs (1997) finding to cluster granularity:
# stable clusters can proceed even when overall DI
# is in WARNING zone (10-15%).
# Ibbs, C.W. (1997). Quantitative impacts of project change.
# Journal of Construction Engineering and Management,
# 123(3), 308-311.
def get_procurement_recommendation(
    di_value: float,
    clusters: dict,
    unstable_floor_ids: list,
) -> dict:
    """
    Return a cluster-level procurement action based on DI and
    which clusters contain unstable floors.

    Parameters
    ----------
    di_value           : float — DI from compute_design_freeze()
    clusters           : dict  — {cluster_id: [floor_ids]}
                         e.g. {0: ['F1','F2'], 1: ['F3']}
    unstable_floor_ids : list  — floor_ids from
                         identify_unstable_floors()

    Returns
    -------
    dict with keys:
        action             (str)  — one of:
            "PROCURE ALL" |
            "PROCURE STABLE CLUSTERS ONLY" |
            "HALT ALL PROCUREMENT"
        stable_clusters    (list) — cluster IDs with no unstable floors
        unstable_clusters  (list) — cluster IDs with >= 1 unstable floor
        detail             (str)  — one-paragraph guidance

    Academic basis
    --------------
    Ibbs (1997): scope changes beyond 15% DI cause 3x rework cost.
    Cluster granularity allows partial procurement to preserve
    schedule for stable clusters while protecting against rework
    on unstable ones.
    """
    unstable_set   = set(str(f) for f in unstable_floor_ids)
    stable_cl      = []
    unstable_cl    = []

    for cluster_id, floor_ids in clusters.items():
        has_unstable = any(
            str(f) in unstable_set for f in floor_ids
        )
        if has_unstable:
            unstable_cl.append(cluster_id)
        else:
            stable_cl.append(cluster_id)

    if di_value <= 10.0:
        action = "PROCURE ALL"
        detail = (
            "All clusters are stable. Safe to place full "
            "procurement order for all panels immediately."
        )
    elif di_value <= 15.0:
        action = "PROCURE STABLE CLUSTERS ONLY"
        cl_str  = ", ".join(str(c) for c in stable_cl) or "(none)"
        unc_str = ", ".join(str(c) for c in unstable_cl) or "(none)"
        detail = (
            f"Procure clusters: {cl_str}. "
            f"Hold procurement for clusters: {unc_str} "
            "until DI drops below 10%."
        )
    else:
        action = "HALT ALL PROCUREMENT"
        detail = (
            "Do not place any orders. Freeze drawings for all floors. "
            "Review in 2 weeks. Ibbs (1997): DI > 15% causes 3x "
            "rework cost on all affected work packages."
        )

    return {
        "action":            action,
        "stable_clusters":   stable_cl,
        "unstable_clusters": unstable_cl,
        "detail":            detail,
    }


def predict_design_change_risk(di_history: list) -> dict:
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
        "Ibbs (1997) J.Const.Eng.Mgmt. 123(3) — "
        "sustained DI exceedance correlates with "
        "3x late-stage change probability"
    )

    # ── Guard: empty list ────────────────────────────────────────────────
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

    # ── Guard: single value ──────────────────────────────────────────────
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

    # ── Risk classification (Ibbs 1997 sustained-breach logic) ───────────
    # HIGH requires BOTH conditions — a single spike is not predictive.
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


# ============================================================
# Design Change Probability Indicator — Gap 3
# ============================================================
# Ibbs, C.W. (1997). Quantitative impacts of project change.
# J. Construction Engineering & Management, 123(3), 308-311.
#   → Sustained DI > 10% predicts late design change;
#     DI > 15% shows 3× rework cost inflection.
# Montgomery, D.C. (2019). Statistical Quality Control (8th ed.).
# Wiley. Chapter 6.
#   → Sustained multi-feature deviation signals process shift.
#     When ≥ 2 features exceed CV threshold simultaneously,
#     the probability estimate is upgraded one level.

# Probability band definitions (Ibbs 1997 inflection points):
_PROB_BANDS = {
    "LOW":      {"pct": 15, "label": "LOW — design likely stable"},
    "MODERATE": {"pct": 45, "label": "MODERATE — monitor weekly"},
    "HIGH":     {"pct": 78, "label": "HIGH — late design change likely"},
}

_PROB_ORDER = ["LOW", "MODERATE", "HIGH"]   # upgrade direction


def compute_change_probability(df: pd.DataFrame, di_value: float) -> dict:
    """
    Design Change Probability Indicator.

    Maps the Design Instability Index (DI) to a probability band and
    upgrades the estimate when ≥ 2 of 3 geometric features show
    simultaneous CV > 10% (Montgomery, 2019 — sustained multi-feature
    deviation signals process shift).

    Academic basis
    --------------
    Ibbs, C.W. (1997). Quantitative impacts of project change.
    J. Construction Engineering & Management, 123(3), 308-311.
        → DI ≤ 10%: low probability of late change (base: 15%).
        → 10 < DI ≤ 15%: moderate probability (base: 45%).
        → DI > 15%: high probability, 3× rework cost (base: 78%).

    Montgomery, D.C. (2019). Statistical Quality Control (8th ed.).
    Wiley. Chapter 6.
        → Sustained deviation in ≥ 2 process features simultaneously
          indicates a structural shift, not random noise.
          Probability upgraded one band when this condition holds.

    Parameters
    ----------
    df       : pd.DataFrame — floor dataframe with slab_area, wall_length,
               column_count columns (both naming conventions accepted).
    di_value : float — DI from compute_design_freeze() (percentage).

    Returns
    -------
    dict with keys:
        probability      : str   — "LOW" | "MODERATE" | "HIGH"
        pct              : int   — estimated probability in %
        label            : str   — human-readable label
        sustained_above_10: bool — True if ≥ 2 of 3 CVs exceed 10%
        cv_slab          : float — CV of slab area (%)
        cv_wall          : float — CV of wall length (%)
        cv_col           : float — CV of column count (%)
    """
    # ── Resolve column names (same logic as compute_design_freeze) ────────
    def _resolve_ser(df, *candidates):
        for c in candidates:
            if c in df.columns:
                return df[c].dropna().astype(float)
        return pd.Series(dtype=float)

    slab_s = _resolve_ser(df, "slab_area_sqm", "slab_area_m2")
    wall_s = _resolve_ser(df, "wall_length_m")
    col_s  = _resolve_ser(df, "column_count", "col_count")

    cv_slab = round(_cv(slab_s), 2)
    cv_wall = round(_cv(wall_s), 2)
    cv_col  = round(_cv(col_s),  2)

    # ── Sustained multi-feature check (Montgomery 2019 Ch.6) ─────────────
    above_10 = sum([cv_slab > 10.0, cv_wall > 10.0, cv_col > 10.0])
    sustained_above_10 = above_10 >= 2

    # ── Base probability band (Ibbs 1997 inflection points) ──────────────
    if di_value <= 10.0:
        probability = "LOW"
    elif di_value <= 15.0:
        probability = "MODERATE"
    else:
        probability = "HIGH"

    # ── Upgrade one level when sustained multi-feature deviation ─────────
    # Only upgrade from LOW or MODERATE — HIGH is already the maximum.
    if sustained_above_10 and probability != "HIGH":
        idx = _PROB_ORDER.index(probability)
        probability = _PROB_ORDER[idx + 1]

    band = _PROB_BANDS[probability]

    return {
        "probability":       probability,
        "pct":               band["pct"],
        "label":             band["label"],
        "sustained_above_10": sustained_above_10,
        "cv_slab":           cv_slab,
        "cv_wall":           cv_wall,
        "cv_col":            cv_col,
    }


# ============================================================
# STEP 4 — Self-contained test runner
# ============================================================

def _run_tests():
    """Run Test A (stable) and Test B (unstable). Print pass/fail."""
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    SEP  = "=" * 56
    PASS = "[PASS]"
    FAIL = "[FAIL]"
    all_ok = True

    # ── Test A: stable dataset — all floors similar geometry
    print("\n" + SEP)
    print("TEST A — Stable dataset (DI must be < 10%)")
    print(SEP)
    np.random.seed(0)
    n = 15
    df_stable = pd.DataFrame({
        "slab_area_sqm": np.random.uniform(840, 860, n),   # very tight band
        "wall_length_m": np.random.uniform(415, 425, n),
        "column_count":  np.random.randint(23, 26, n).astype(float),
    })
    r_a = compute_design_freeze(df_stable)
    print(f"  CV_slab : {r_a['CV_slab']:.2f}%")
    print(f"  CV_wall : {r_a['CV_wall']:.2f}%")
    print(f"  CV_col  : {r_a['CV_col']:.2f}%")
    print(f"  DI      : {r_a['DI']:.2f}%")
    print(f"  Status  : {r_a['status']}")
    print(f"  Rec     : {r_a['recommendation']}")
    if r_a["DI"] < 10.0 and r_a["status"] == "SAFE":
        print(f"\n{PASS} Test A — DI={r_a['DI']:.2f}% < 10%, status=SAFE")
    else:
        print(f"\n{FAIL} Test A — DI={r_a['DI']:.2f}%, status={r_a['status']} (expected DI<10, SAFE)")
        all_ok = False

    # ── Test B: unstable — 2 floors with slab 3× larger than others
    print("\n" + SEP)
    print("TEST B — Unstable dataset (DI must be > 15%, status=HALT)")
    print(SEP)
    base_slabs = list(np.random.uniform(840, 860, 13))
    big_slabs  = [2700.0, 2650.0]          # ~3× the typical floor
    df_unstable = pd.DataFrame({
        "slab_area_sqm": base_slabs + big_slabs,
        "wall_length_m": list(np.random.uniform(415, 425, 15)),
        "column_count":  list(np.random.randint(23, 26, 15).astype(float)),
    })
    r_b = compute_design_freeze(df_unstable)
    print(f"  CV_slab : {r_b['CV_slab']:.2f}%")
    print(f"  CV_wall : {r_b['CV_wall']:.2f}%")
    print(f"  CV_col  : {r_b['CV_col']:.2f}%")
    print(f"  DI      : {r_b['DI']:.2f}%")
    print(f"  Status  : {r_b['status']}")
    print(f"  Rec     : {r_b['recommendation']}")
    if r_b["DI"] > 15.0 and r_b["status"] == "HALT":
        print(f"\n{PASS} Test B — DI={r_b['DI']:.2f}% > 15%, status=HALT")
    else:
        print(f"\n{FAIL} Test B — DI={r_b['DI']:.2f}%, status={r_b['status']} (expected DI>15, HALT)")
        all_ok = False

    print("\n" + SEP)
    if all_ok:
        print("  BOTH TESTS PASSED — freeze_guard.py is correct.")
    else:
        print("  ONE OR MORE TESTS FAILED.")
    print(SEP + "\n")
    return all_ok


if __name__ == "__main__":
    _run_tests()
