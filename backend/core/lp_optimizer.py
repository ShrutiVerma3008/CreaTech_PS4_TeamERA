"""
backend/core/lp_optimizer.py
FormOptiX — SKU-Level LP BoQ Optimizer

Academic basis:
  Hillier, F.S., & Lieberman, G.J. (2021). Introduction to Operations Research
    (11th ed.). McGraw-Hill. Chapter 3.
    → LP objective function: minimize weighted sum of procurement + holding + idle costs.
  Biruk, S., & Jaskowski, P. (2017). Scheduling linear construction projects with
    wind-up constraints using a linear programming model. Archives of Civil Engineering,
    63(1).
    → LP applied to construction resource procurement; validates per-week decision
      variable structure.
  Mitchell, S., O'Sullivan, M., & Dunning, I. (2011). PuLP: A linear programming
    toolkit for Python. University of Auckland.
    → Solver implementation reference.
  Forrest, J., & Lougee-Heimer, R. (2005). CBC user guide.
    In Emerging theory, methods, and applications. INFORMS.
    → CBC solver: academically validated, license-free.
"""

import pandas as pd
import numpy as np

try:
    import pulp
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _run_sku_lp(
    sku: str,
    demand_by_week: dict,
    reuse_by_week: dict,
    c_p: float,
    c_h: float,
    c_i: float,
) -> list | dict:
    """
    Run a single SKU LP subproblem and return either a list of result dicts
    (one per week) or an error dict if the solver fails.

    Parameters
    ----------
    sku           : panel type label (e.g. "ALU-600")
    demand_by_week: {week: demand_count}
    reuse_by_week : {week: reuse_count}  — panels physically eligible for reuse
    c_p           : procurement cost per panel (₹)
    c_h           : holding cost per panel per week (₹)
    c_i           : idle cost per panel per week (₹)
    """
    weeks = sorted(demand_by_week.keys())
    demand = [demand_by_week.get(w, 0) for w in weeks]
    reuse  = [reuse_by_week.get(w, 0)  for w in weeks]
    n      = len(weeks)
    total_demand_sku = max(1, sum(demand))  # C3 cap

    # ── LP formulation — Hillier & Lieberman (2021) Ch.3 ──────────────────
    prob = pulp.LpProblem(f"BoQ_{sku}", pulp.LpMinimize)

    x = [pulp.LpVariable(f"procure_w{w}", lowBound=0) for w in range(n)]
    h = [pulp.LpVariable(f"hold_w{w}",    lowBound=0) for w in range(n)]
    i = [pulp.LpVariable(f"idle_w{w}",    lowBound=0) for w in range(n)]

    # Objective: minimise total cost (procurement + holding + idle)
    prob += pulp.lpSum([c_p * x[w] + c_h * h[w] + c_i * i[w] for w in range(n)])

    for w in range(n):
        prev_h = h[w - 1] if w > 0 else 0

        # C1 — Demand satisfaction
        prob += x[w] + reuse[w] + prev_h >= demand[w], f"C1_demand_w{w}"

        # C2 — Inventory balance (carry-over)
        prob += h[w] == (x[w] + reuse[w] + prev_h) - demand[w], f"C2_balance_w{w}"

        # C3 — Purchase cap (demand-derived, not hardcoded)
        prob += x[w] <= total_demand_sku, f"C3_cap_w{w}"

    # ── CBC solver — Forrest & Lougee-Heimer (2005) ───────────────────────
    solver = pulp.PULP_CBC_CMD(msg=0)
    prob.solve(solver)
    status = pulp.LpStatus[prob.status]

    if status != "Optimal":
        return {
            "status": status,
            "error": (
                f"LP solver returned '{status}' for SKU '{sku}'. "
                "Check demand inputs and cost parameters."
            ),
            "sku": sku,
        }

    rows = []
    for w in range(n):
        proc_val = pulp.value(x[w]) or 0.0
        hold_val = pulp.value(h[w]) or 0.0
        idle_val = pulp.value(i[w]) or 0.0
        rows.append({
            "sku":       sku,
            "week":      int(weeks[w]),
            "procure":   round(proc_val),
            "reuse":     round(reuse[w]),
            "hold":      round(hold_val),
            "idle":      round(idle_val),
            "week_cost": round(c_p * proc_val + c_h * hold_val + c_i * idle_val),
        })
    return rows


def _jit_fallback(
    sku: str,
    demand_by_week: dict,
    reuse_by_week: dict,
    c_p: float,
    c_h: float,
    c_i: float,
) -> list:
    """
    Just-in-time heuristic when PuLP is unavailable.
    Procures exactly what is needed each week (demand - reuse), no carry.
    """
    rows = []
    for w in sorted(demand_by_week.keys()):
        d = demand_by_week.get(w, 0)
        r = reuse_by_week.get(w, 0)
        proc = max(0, d - r)
        rows.append({
            "sku":       sku,
            "week":      int(w),
            "procure":   proc,
            "reuse":     r,
            "hold":      0,
            "idle":      0,
            "week_cost": round(c_p * proc),
        })
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# Public interface
# ──────────────────────────────────────────────────────────────────────────────

def compute_baseline(df_schedule: pd.DataFrame, c_p: float, **_) -> float:
    """
    Baseline cost: procure every panel fresh every week, no reuse, no holding.
    Represents a site with zero algorithmic planning.

    Parameters
    ----------
    df_schedule : schedule DataFrame with columns [week, *_panels_demand]
    c_p         : procurement cost per panel (₹)
    """
    total = 0.0
    for col in df_schedule.columns:
        if col.endswith("_panels_demand"):
            total += c_p * df_schedule[col].sum()
    return total


def run_sku_optimizer(
    df_schedule: pd.DataFrame,
    df_floors: pd.DataFrame | None,
    c_p: float,
    c_h: float,
    c_i: float,
    monthly_budget_cr: float = 8.0,
) -> dict:
    """
    Run SKU-level LP optimisation.

    Parameters
    ----------
    df_schedule       : DataFrame with columns [week, wall_panels_demand,
                        slab_panels_demand, col_panels_demand]
    df_floors         : floor DataFrame (used to build reuse vectors if available)
    c_p               : procurement cost per panel (₹)
    c_h               : holding cost per panel per week (₹)
    c_i               : idle cost per panel per week (₹)
    monthly_budget_cr : informational only — not used as a hard constraint

    Returns
    -------
    dict with keys:
        status          : "Optimal" | "Heuristic (PuLP not installed)" | error str
        boq_results     : list of per-SKU per-week dicts
        optimized_total : int  — total LP cost (₹)
        baseline_total  : int  — total baseline cost (₹)
        savings         : int  — baseline − optimised (₹)
        savings_pct     : float
        trad_total      : alias for baseline_total (backward compat)
        opt_total       : alias for optimized_total (backward compat)
        # legacy chart fields:
        opt_buy_w, opt_buy_s, demand_w, demand_s,
        trad_inv_w, opt_inv_w, trad_inv_s, opt_inv_s
    """
    weeks    = df_schedule["week"].values
    demand_w = df_schedule["wall_panels_demand"].values
    demand_s = df_schedule["slab_panels_demand"].values
    demand_c = df_schedule["col_panels_demand"].values

    skus_data = {
        "wall": {int(w): int(d) for w, d in zip(weeks, demand_w)},
        "slab": {int(w): int(d) for w, d in zip(weeks, demand_s)},
        "col":  {int(w): int(d) for w, d in zip(weeks, demand_c)},
    }

    # ── Reuse Vector Derivation ──────────────────────────────────────────
    tw = 1  # transport_weeks — Hanna (1998) Ch.4
    reuse_data = {sku: {int(w): 0 for w in weeks} for sku in skus_data}

    if df_floors is not None and "strip_week" in df_floors.columns:
        for _, row in df_floors.iterrows():
            sw = row.get("strip_week")
            if pd.isna(sw):
                continue
            avail_w = int(sw) + tw
            if avail_w in weeks:
                reuse_data["wall"][avail_w] += int(row.get("wall_panels", 0))
                reuse_data["slab"][avail_w] += int(row.get("slab_panels", 0))
                reuse_data["col"][avail_w]  += int(row.get("col_panels", 0))

    all_boq_rows: list = []
    overall_status = "Optimal"
    optimized_total = 0

    if PULP_AVAILABLE:
        for sku, demand_by_week in skus_data.items():
            result = _run_sku_lp(sku, demand_by_week, reuse_data[sku], c_p, c_h, c_i)
            if isinstance(result, dict) and "error" in result:
                return {
                    "status":          result["status"],
                    "error":           result["error"],
                    "boq_results":     [],
                    "optimized_total": 0,
                    "baseline_total":  0,
                    "savings":         0,
                    "savings_pct":     0,
                    "trad_total": 0, "opt_total": 0,
                    "opt_buy_w": [], "opt_buy_s": [],
                    "demand_w": demand_w, "demand_s": demand_s,
                    "trad_inv_w": [], "opt_inv_w": [],
                    "trad_inv_s": [], "opt_inv_s": [],
                }
            all_boq_rows.extend(result)
            optimized_total += sum(r["week_cost"] for r in result)
    else:
        overall_status = "Heuristic (PuLP not installed)"
        for sku, demand_by_week in skus_data.items():
            rows = _jit_fallback(sku, demand_by_week, reuse_data[sku], c_p, c_h, c_i)
            all_boq_rows.extend(rows)
            optimized_total += sum(r["week_cost"] for r in rows)

    baseline_total = compute_baseline(df_schedule, c_p)
    savings        = baseline_total - optimized_total
    savings_pct    = (savings / baseline_total * 100) if baseline_total > 0 else 0

    # ── Backward-compatible chart fields ─────────────────────────────────
    opt_buy_w = [
        next((r["procure"] for r in all_boq_rows if r["sku"] == "wall" and r["week"] == int(w)), 0)
        for w in weeks
    ]
    opt_buy_s = [
        next((r["procure"] for r in all_boq_rows if r["sku"] == "slab" and r["week"] == int(w)), 0)
        for w in weeks
    ]

    trad_buy_w = [int(d * 1.20) for d in demand_w]
    trad_buy_s = [int(d * 1.20) for d in demand_s]
    trad_inv_w = [max(0, sum(trad_buy_w[:t+1]) - int(sum(demand_w[:t+1]))) for t in range(len(weeks))]
    trad_inv_s = [max(0, sum(trad_buy_s[:t+1]) - int(sum(demand_s[:t+1]))) for t in range(len(weeks))]
    opt_inv_w  = [max(0, sum(opt_buy_w[:t+1])  - int(sum(demand_w[:t+1]))) for t in range(len(weeks))]
    opt_inv_s  = [max(0, sum(opt_buy_s[:t+1])  - int(sum(demand_s[:t+1]))) for t in range(len(weeks))]

    trad_proc = c_p * (sum(trad_buy_w) + sum(trad_buy_s) + int(sum(demand_c)))

    return {
        "status":           overall_status,
        "boq_results":      all_boq_rows,
        "optimized_total":  int(optimized_total),
        "baseline_total":   int(baseline_total),
        "savings":          int(savings),
        "savings_pct":      round(savings_pct, 2),
        # backward-compat aliases
        "trad_total":   int(baseline_total),
        "opt_total":    int(optimized_total),
        "trad_proc":    int(baseline_total),
        "trad_hold":    0,
        "trad_idle":    0,
        "opt_proc":     int(optimized_total),
        "opt_hold":     0,
        "opt_idle":     0,
        # chart arrays
        "opt_buy_w":  opt_buy_w,
        "opt_buy_s":  opt_buy_s,
        "demand_w":   demand_w,
        "demand_s":   demand_s,
        "trad_inv_w": trad_inv_w,
        "trad_inv_s": trad_inv_s,
        "opt_inv_w":  opt_inv_w,
        "opt_inv_s":  opt_inv_s,
    }
