"""
frontend/pages/building_data.py
Tab 4 — Building Data: floor type donut, geometry scatter, full data table.
"""

import streamlit as st
from frontend.charts import make_floor_type_donut, make_geometry_scatter
from frontend.theme import ORANGE


def render(state: dict) -> None:
    df_floors = state["df_floors"]
    n_floors  = state["n_floors"]

    st.markdown(
        "<div class='section-header'>🏗️ Floor-by-Floor Data (Module 1 — Synthetic Dataset)</div>",
        unsafe_allow_html=True,
    )
    col_donut, col_scatter = st.columns([1, 2])
    with col_donut:
        st.plotly_chart(make_floor_type_donut(df_floors, n_floors), use_container_width=True)
    with col_scatter:
        st.plotly_chart(make_geometry_scatter(df_floors), use_container_width=True)

    st.markdown("**Complete Floor Dataset**")
    display_cols = [c for c in [
        "floor_name", "floor_type", "slab_area_sqm", "slab_area_m2",
        "wall_length_m", "column_count", "col_count", "beam_count", "cluster", "rho_k",
    ] if c in df_floors.columns]
    st.dataframe(
        df_floors[display_cols].style.apply(
            lambda col: [
                f"color: {ORANGE}; font-weight:bold;" if v == "Typical" else ""
                for v in col
            ] if col.name == "floor_type" else [""] * len(col),
            axis=0,
        ),
        use_container_width=True, hide_index=True, height=360,
    )
