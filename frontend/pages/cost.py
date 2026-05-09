"""
frontend/pages/cost.py
Tab 2 — Cost Optimization: ROI counter, cost comparison, waterfall, LP details.
"""

import streamlit as st

from frontend.charts import make_cost_comparison, make_roi_waterfall, make_utilization_bars
from frontend.theme import GREEN, TEAL, AMBER, RED, ORANGE, TEXT


def render(state: dict) -> None:
    """
    Render Tab 2 — Cost Optimization.

    Parameters
    ----------
    state : dict with keys: lp_results, savings_cr, trad_total_cr,
                            opt_total_cr, saving_pct, project_cost, monthly_budget
    """
    lp_results    = state["lp_results"]
    savings_cr    = state["savings_cr"]
    trad_total_cr = state["trad_total_cr"]
    opt_total_cr  = state["opt_total_cr"]
    saving_pct    = state["saving_pct"]
    project_cost  = state["project_cost"]
    monthly_budget = state["monthly_budget"]

    # ── ROI Counter ──────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>💵 ROI Counter</div>", unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)

    cards = [
        (r1, f"₹{savings_cr:.2f} Cr", "Total Projected Savings",
         f"per ₹{project_cost} Cr project", GREEN, GREEN),
        (r2, f"₹{trad_total_cr:.2f} Cr", "Traditional Formwork Cost",
         "without optimization", RED, None),
        (r3, f"₹{opt_total_cr:.2f} Cr", "FormOptiX Optimized Cost",
         "LP-optimized procurement", TEAL, TEAL),
        (r4, f"{saving_pct:.1f}%", "Cost Reduction",
         "vs manual planning", AMBER, GREEN),
    ]
    for col, val, label, delta, val_color, border_color in cards:
        border_css = f"border-color:{border_color};" if border_color else ""
        col.markdown(f"""
        <div class='metric-card' style='{border_css}'>
          <div class='metric-value' style='color:{val_color};'>{val}</div>
          <div class='metric-label'>{label}</div>
          <div class='metric-delta-pos'>{delta}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ───────────────────────────────────────────────────────────
    col_bar, col_wfall = st.columns(2)
    with col_bar:
        st.plotly_chart(make_cost_comparison(lp_results), use_container_width=True)
    with col_wfall:
        st.plotly_chart(make_roi_waterfall(savings_cr, trad_total_cr, opt_total_cr),
                        use_container_width=True)

    st.plotly_chart(make_utilization_bars(), use_container_width=True)

    # ── LP Solver Details ────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🔩 LP Optimizer Details</div>", unsafe_allow_html=True)
    lp_c1, lp_c2 = st.columns(2)
    with lp_c1:
        st.markdown(f"""
        <div class='callout-teal'>
          <b>Optimization Model</b><br>
          <span style='font-family:monospace; font-size:0.85rem; color:#79C0FF;'>
            Minimize: Σ(procurement_cost × x[t]) + Σ(holding_cost × inventory[t])<br><br>
            Subject to:<br>
            C1: inventory[t] ≥ demand[t] ∀t<br>
            C2: Σ(panels_reused) ≤ reuse_limit<br>
            C3: weekly_spend ≤ ₹{monthly_budget/4.33:.1f} Cr
          </span>
        </div>
        """, unsafe_allow_html=True)
    with lp_c2:
        st.markdown(f"""
        <table class='custom-table'>
          <tr><th>Cost Component</th><th>Traditional</th><th>FormOptiX</th><th>Saving</th></tr>
          <tr>
            <td>Procurement</td>
            <td>₹{lp_results["trad_proc"]/1e7:.2f} Cr</td>
            <td class='td-green'>₹{lp_results["opt_proc"]/1e7:.2f} Cr</td>
            <td class='td-green'>₹{(lp_results["trad_proc"]-lp_results["opt_proc"])/1e7:.2f} Cr</td>
          </tr>
          <tr>
            <td>Holding Cost</td>
            <td>₹{lp_results["trad_hold"]/1e7:.2f} Cr</td>
            <td class='td-green'>₹{lp_results["opt_hold"]/1e7:.2f} Cr</td>
            <td class='td-green'>₹{(lp_results["trad_hold"]-lp_results["opt_hold"])/1e7:.2f} Cr</td>
          </tr>
          <tr>
            <td>Idle Inventory</td>
            <td>₹{lp_results["trad_idle"]/1e7:.2f} Cr</td>
            <td class='td-green'>₹{lp_results["opt_idle"]*0.3/1e7:.2f} Cr</td>
            <td class='td-green'>₹{(lp_results["trad_idle"]-lp_results["opt_idle"]*0.3)/1e7:.2f} Cr</td>
          </tr>
          <tr>
            <td class='td-orange'><b>TOTAL</b></td>
            <td><b>₹{trad_total_cr:.2f} Cr</b></td>
            <td class='td-green'><b>₹{opt_total_cr:.2f} Cr</b></td>
            <td class='td-green'><b>₹{savings_cr:.2f} Cr</b></td>
          </tr>
        </table>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='font-size:0.78rem; color:#7B8A9E; margin-top:12px; font-style:italic;'>
      * Projections based on simulation modelled on industry benchmarks (CIDC, L&T internal norms).
      Pilot validation planned for Phase 1. LP Solver status: <b>{lp_results["status"]}</b>
    </div>
    """, unsafe_allow_html=True)
