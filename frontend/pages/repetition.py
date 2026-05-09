"""
frontend/pages/repetition.py
Tab 1 — Repetition Analysis: DBSCAN gauge, cluster chart, heatmap, design freeze.
"""

import numpy as np
import streamlit as st

from frontend.charts import (
    make_gauge, make_cluster_chart, make_floor_heatmap, make_design_revision_chart,
)
from frontend.theme import GREEN, AMBER, RED, ORANGE, TEXT


def render(state: dict) -> None:
    """
    Render Tab 1 — Repetition Analysis.

    Parameters
    ----------
    state : dict extracted from st.session_state by app.py
        Required keys: df_floors, cluster_summary, rep_score,
                       repetition_threshold, seed, rho_k_map, reuse_pairs
    """
    df_floors           = state["df_floors"]
    cluster_summary     = state["cluster_summary"]
    rep_score           = state["rep_score"]
    threshold           = state["repetition_threshold"]
    seed                = state["seed"]
    rho_k_map           = state.get("rho_k_map", {})
    reuse_pairs         = state.get("reuse_pairs", [])

    # ── Gauge + Cluster bubble chart ────────────────────────────────────
    col_gauge, col_cluster = st.columns([1, 2])

    with col_gauge:
        st.plotly_chart(make_gauge(rep_score, threshold), use_container_width=True)

        st.markdown("""
        <div class='callout-orange' style='margin-top:8px;'>
          <b>How it works</b><br>
          DBSCAN clusters floors by similarity of slab area, wall length, column &amp; beam count.
          Floors in the dominant cluster can share formwork panels — maximizing reuse.
        </div>
        """, unsafe_allow_html=True)

        # Cluster summary table
        st.markdown("**Cluster Summary**")
        rows_html = "".join([
            f"<tr><td class='td-orange'>{row.cluster if row.cluster >= 0 else 'Outlier'}</td>"
            f"<td>{row['count']}</td>"
            f"<td>{row.avg_slab:.1f}</td>"
            f"<td>{row.avg_wall:.1f}</td></tr>"
            for _, row in cluster_summary.iterrows()
        ])
        st.markdown(f"""
        <table class='custom-table'>
          <tr><th>Cluster</th><th>Floor Count</th><th>Avg Slab (sqm)</th><th>Avg Wall (m)</th></tr>
          {rows_html}
        </table>
        """, unsafe_allow_html=True)

    with col_cluster:
        st.plotly_chart(make_cluster_chart(df_floors), use_container_width=True)

    # ── Floor-type heatmap ───────────────────────────────────────────────
    st.plotly_chart(make_floor_heatmap(df_floors), use_container_width=True)

    # ── Physical Reuse Pairs table (only when schedule data present) ─────
    if reuse_pairs:
        st.markdown("<div class='section-header'>🔗 Physically Valid Reuse Pairs</div>",
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div class='callout-teal'>
          <b>{len(reuse_pairs)} valid panel-reuse opportunities identified</b> after applying the
          ACI 347R-14 strip-time + transport constraint (Hanna, 1998, Ch.4).
        </div>
        """, unsafe_allow_html=True)

        import pandas as pd
        df_pairs = pd.DataFrame(reuse_pairs[:20])  # show first 20
        st.dataframe(df_pairs, use_container_width=True, hide_index=True)

    # ── Reuse coefficient per cluster ────────────────────────────────────
    if rho_k_map:
        st.markdown("<div class='section-header'>📊 Reuse Coefficient (ρ_k) per Cluster</div>",
                    unsafe_allow_html=True)
        for k, rho in rho_k_map.items():
            color = GREEN if rho >= 0.6 else (AMBER if rho >= 0.3 else RED)
            st.markdown(
                f"<span style='color:{color}; font-family:monospace;'>"
                f"Cluster {k}: ρ_k = {rho:.1%}</span> "
                f"{'✅ Industry benchmark met' if rho >= 0.6 else '⚠️ Below 60% benchmark'}",
                unsafe_allow_html=True,
            )

    # ── Design Freeze Intelligence ───────────────────────────────────────
    st.markdown("<div class='section-header'>🔒 Design Freeze Intelligence</div>",
                unsafe_allow_html=True)
    st.markdown("""
    <div class='callout-teal'>
      <b>Simulating 3 design revision cycles...</b><br>
      FormOptiX monitors BIM version history and recalculates Repetition Score after each revision.
    </div>
    """, unsafe_allow_html=True)

    np.random.seed(int(seed))
    v1 = rep_score
    v2 = rep_score + np.random.uniform(-8, 5)
    v3 = v2 + np.random.uniform(-12, 3)

    versions = ["Design v1.0", "Design v2.0\n(Window revision)", "Design v3.0\n(Slab change)"]
    fig_dfi  = make_design_revision_chart([v1, v2, v3], versions, threshold)
    st.plotly_chart(fig_dfi, use_container_width=True)

    drop = v1 - v3
    if drop > 15:
        st.markdown(f"""
        <div class='callout-red'>
          <b>⚠️ PROCUREMENT HOLD RECOMMENDED</b><br>
          Design churn detected. Repetition Score dropped from <b>{v1:.1f}%</b> to <b>{v3:.1f}%</b>
          (Δ = {drop:.1f}pp). Delaying panel ordering until design stabilizes will prevent
          excess procurement.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='callout-green'>
          <b>✅ Design Stable</b><br>
          Score variation {drop:.1f}pp is within acceptable range. Procurement can proceed.
        </div>
        """, unsafe_allow_html=True)
