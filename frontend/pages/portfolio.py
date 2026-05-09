"""
frontend/pages/portfolio.py
Tab 6 — Cross-Site Portfolio: demonstrates reallocation of idle panels across sites.
"""

import streamlit as st
import pandas as pd
from frontend.theme import TEAL, ORANGE, GREEN, MUTED, RED
from backend.core.cross_site import collect_idle_panels, match_supply_to_demand

def render(state: dict) -> None:
    st.markdown("<div class='section-header'>🌍 Cross-Site Portfolio Optimization</div>",
                unsafe_allow_html=True)
    
    st.markdown("""
    <div class='callout-teal'>
      <b>Network-level Reallocation</b><br>
      Instead of each site buying fresh formwork, FormOptiX scans the enterprise portfolio 
      for idle panels and mathematically matches them to upcoming demand at other sites.
    </div>
    """, unsafe_allow_html=True)

    # We use a synthetic 3-site scenario to demonstrate this, 
    # anchoring one site to the current project's cost parameters.
    c_p = state.get("cost_params", {}).get("c_p", 15000)

    # 1. Generate synthetic portfolio data
    idle_data = [
        {"site": "Site A (Current)", "sku": "Wall Panel 600mm", "week": 12, "idle_qty": 150},
        {"site": "Site A (Current)", "sku": "Slab Panel 1.5sqm", "week": 15, "idle_qty": 300},
        {"site": "Site B (Mumbai)", "sku": "Wall Panel 600mm", "week": 8, "idle_qty": 80},
        {"site": "Site C (Delhi)", "sku": "Column Panel", "week": 10, "idle_qty": 40},
    ]
    
    demand_data = [
        {"site": "Site B (Mumbai)", "sku": "Wall Panel 600mm", "week": 14, "procure_qty": 100},
        {"site": "Site C (Delhi)", "sku": "Slab Panel 1.5sqm", "week": 18, "procure_qty": 250},
        {"site": "Site A (Current)", "sku": "Column Panel", "week": 12, "procure_qty": 30},
    ]

    col_idle, col_demand = st.columns(2)
    with col_idle:
        st.markdown("**Idle Inventory Pool (Supply)**")
        st.dataframe(pd.DataFrame(idle_data), use_container_width=True, hide_index=True)
    with col_demand:
        st.markdown("**Upcoming Procurement Needs (Demand)**")
        st.dataframe(pd.DataFrame(demand_data), use_container_width=True, hide_index=True)

    # 2. Run the matcher
    matches = match_supply_to_demand(idle_data, demand_data)
    
    # Calculate savings
    total_panels_saved = 0
    total_cost_saved = 0.0
    for m in matches:
        m["saving_rs"] = m["qty"] * c_p
        total_panels_saved += m["qty"]
        total_cost_saved += m["saving_rs"]

    st.markdown("<div class='section-header'>🔗 Reallocation Matches Found</div>",
                unsafe_allow_html=True)
    
    if matches:
        # Display summary metrics
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"""
        <div class='metric-card'>
          <div class='metric-value' style='color:{TEAL};'>{len(matches)}</div>
          <div class='metric-label'>Matches Found</div>
        </div>
        """, unsafe_allow_html=True)
        m2.markdown(f"""
        <div class='metric-card'>
          <div class='metric-value' style='color:{ORANGE};'>{total_panels_saved}</div>
          <div class='metric-label'>Panels Reallocated</div>
        </div>
        """, unsafe_allow_html=True)
        m3.markdown(f"""
        <div class='metric-card'>
          <div class='metric-value' style='color:{GREEN};'>₹{total_cost_saved/100000:,.1f} L</div>
          <div class='metric-label'>Procurement Avoided</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>**Transfer Logistics**", unsafe_allow_html=True)
        
        # Display visual routes
        for m in matches:
            st.markdown(f"""
            <div style='background:#111827; border-left:4px solid {GREEN}; padding:12px; margin-bottom:8px; border-radius:6px;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div style='flex:1;'>
                        <div style='color:{MUTED}; font-size:0.8rem;'>FROM</div>
                        <div style='font-weight:bold; color:{TEXT};'>{m['from_site']}</div>
                        <div style='color:{MUTED}; font-size:0.8rem;'>Available: Wk {m['available_week']}</div>
                    </div>
                    <div style='flex:1; text-align:center;'>
                        <div style='color:{ORANGE}; font-weight:bold;'>{m['qty']}x {m['sku']}</div>
                        <div style='color:{GREEN}; font-size:0.9rem;'>⬇️ Saves ₹{m['saving_rs']/100000:.1f} Lakhs</div>
                    </div>
                    <div style='flex:1; text-align:right;'>
                        <div style='color:{MUTED}; font-size:0.8rem;'>TO</div>
                        <div style='font-weight:bold; color:{TEXT};'>{m['to_site']}</div>
                        <div style='color:{MUTED}; font-size:0.8rem;'>Needed: Wk {m['needed_week']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No cross-site matches found in this scenario.")
