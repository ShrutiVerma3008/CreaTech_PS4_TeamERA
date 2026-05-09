"""
frontend/pages/inventory.py
Tab 3 — Inventory & Forecast: inventory curve, forecast chart, data source cards,
         weekly procurement table, PDF export.
"""

import pandas as pd
import streamlit as st

from frontend.charts import make_inventory_curve, make_forecast_chart
from backend.utils.report_generator import generate_boq_pdf


def render(state: dict) -> None:
    """
    Render Tab 3 — Inventory & Forecast.

    Parameters
    ----------
    state : dict with keys: lp_results, df_schedule, forecast_data,
                            boq_results, cost_params, project_name,
                            di_value, di_status, overall_reuse_rate
    """
    lp_results    = state["lp_results"]
    df_schedule   = state["df_schedule"]
    weeks_arr     = df_schedule["week"].values
    forecast_data = state["forecast_data"]
    boq_results   = state.get("boq_results", [])
    cost_params   = state.get("cost_params", {})
    project_name  = state.get("project_name", "FormOptiX Project")

    weeks_f, demand_f, forecast_f, upper_f, lower_f = forecast_data

    # ── Charts ───────────────────────────────────────────────────────────
    st.plotly_chart(make_inventory_curve(lp_results, weeks_arr), use_container_width=True)
    st.plotly_chart(make_forecast_chart(weeks_f, demand_f, forecast_f, upper_f, lower_f),
                    use_container_width=True)

    # ── Data Source Strategy ─────────────────────────────────────────────
    st.markdown("<div class='section-header'>📋 Data Source Strategy (M4)</div>",
                unsafe_allow_html=True)
    ds_c1, ds_c2, ds_c3, ds_c4 = st.columns(4)
    ds_items = [
        (ds_c1, "Phase 1",    "L&T Internal DB",  "Historical formwork demand logs from past projects",    "phase-1"),
        (ds_c2, "Phase 2",    "BIM Exports",      "Revit/Navisworks timeline exports → auto demand curve", "phase-2"),
        (ds_c3, "Phase 3",    "RFID/IoT",         "Real-time panel tracking feeds model continuously",     "phase-2"),
        (ds_c4, "Cold Start", "Floor Area Rule",   "panels = floor_area / 12 (physics-based fallback)",    "phase-0"),
    ]
    for col, phase, src, desc, cls in ds_items:
        col.markdown(f"""
        <div class='metric-card'>
          <span class='phase-badge {cls}'>{phase}</span>
          <div style='font-weight:600; color:#E8EDF5; margin-top:8px;'>{src}</div>
          <div style='font-size:0.8rem; color:#7B8A9E; margin-top:4px;'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Weekly Procurement Table ─────────────────────────────────────────
    st.markdown("<div class='section-header'>📅 Sample Weekly Procurement Plan (FormOptiX)</div>",
                unsafe_allow_html=True)
    sample_weeks = list(range(0, min(10, len(df_schedule))))
    tbl_data = {
        "Week":               [df_schedule.iloc[i]["week"] for i in sample_weeks],
        "Wall Demand":        [lp_results["demand_w"][i] for i in sample_weeks],
        "Wall Optimized Buy": [lp_results["opt_buy_w"][i] for i in sample_weeks],
        "Wall Inventory":     [round(lp_results["opt_inv_w"][i]) for i in sample_weeks],
        "Slab Demand":        [lp_results["demand_s"][i] for i in sample_weeks],
        "Slab Optimized Buy": [lp_results["opt_buy_s"][i] for i in sample_weeks],
    }
    df_tbl = pd.DataFrame(tbl_data)
    st.dataframe(
        df_tbl.style.background_gradient(
            subset=["Wall Optimized Buy", "Slab Optimized Buy"],
            cmap="YlOrRd",
        ),
        use_container_width=True,
        hide_index=True,
    )

    # ── PDF BoQ Export ───────────────────────────────────────────────────
    if boq_results:
        st.markdown("<div class='section-header'>📄 Export Bill of Quantities (PDF)</div>",
                    unsafe_allow_html=True)

        boq_df      = pd.DataFrame(boq_results)
        delivery_df = boq_df[boq_df["procure"] > 0].copy()
        if "estimated_delivery_week" not in delivery_df.columns:
            delivery_df["estimated_delivery_week"] = delivery_df["week"] + 1

        opt_total_cr = lp_results["opt_total"] / 1e7
        base_total_cr = lp_results["trad_total"] / 1e7
        savings_cr    = (lp_results["trad_total"] - lp_results["opt_total"]) / 1e7
        savings_pct   = (savings_cr / base_total_cr * 100) if base_total_cr > 0 else 0

        metrics = {
            "optimized_cr":      opt_total_cr,
            "baseline_cr":       base_total_cr,
            "savings_cr":        savings_cr,
            "savings_pct":       savings_pct,
            "overall_reuse_rate": state.get("overall_reuse_rate", 0.0),
            "di_value":          state.get("di_value", 0.0),
            "di_status":         state.get("di_status", "N/A"),
        }

        try:
            pdf_bytes = generate_boq_pdf(boq_df, delivery_df, metrics, project_name)
            st.download_button(
                label="⬇️  Download BoQ PDF",
                data=pdf_bytes,
                file_name=f"FormOptiX_BoQ_{project_name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"PDF generation failed: {e}. Install reportlab to enable PDF export.")
