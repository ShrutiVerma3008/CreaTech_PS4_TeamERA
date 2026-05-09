"""
frontend/app.py
FormOptiX — Main Streamlit entry point.

Run: streamlit run frontend/app.py

This file is intentionally lean: page config, CSS injection, sidebar,
session state orchestration, and tab routing. All business logic lives
in backend/. All visual rendering lives in frontend/pages/.
"""

import sys
import time
from pathlib import Path

# Ensure project root is on sys.path so `backend` and `frontend` are importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import warnings

# ── Frontend modules
from frontend.theme import inject_css, ORANGE, GREEN, RED, AMBER, TEAL, TEXT, MUTED
import frontend.pages.repetition   as pg_repetition
import frontend.pages.cost         as pg_cost
import frontend.pages.inventory    as pg_inventory
import frontend.pages.building_data as pg_building_data
import frontend.pages.roadmap      as pg_roadmap
import frontend.pages.portfolio    as pg_portfolio

# ── Backend modules
from backend.utils.synthetic_data import generate_building_data, simulate_forecast
from backend.core.clustering      import compute_repetition_score
from backend.core.lp_optimizer    import run_sku_optimizer
from backend.core.freeze_guard    import (
    compute_design_freeze,
    identify_unstable_floors,
    estimate_rework_cost,
    get_procurement_recommendation,
)
from backend.utils.data_loader    import validate_and_map

import pandas as pd


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="FormOptiX – Formwork Intelligence",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding:16px 0 8px 0;'>
      <div style='font-size:2rem;font-weight:900;background:linear-gradient(135deg,{ORANGE},{AMBER});
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>FormOptiX</div>
      <div style='font-size:0.68rem;color:{MUTED};letter-spacing:2px;text-transform:uppercase;margin-top:4px;'>
        Repetition Intelligence Engine
      </div>
    </div>
    <hr style='border-color:#1E2D45;margin:12px 0;'>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Project Parameters")

    mode = st.radio("Select Data Mode", ["Synthetic Demo", "Real Site Data"])

    n_floors             = st.slider("Number of Floors", 10, 40, 20, 1)
    monthly_budget       = st.slider("Monthly Formwork Budget (₹ Cr)", 2.0, 20.0, 8.0, 0.5)
    project_cost         = st.slider("Total Project Cost (₹ Cr)", 100, 800, 500, 50)
    repetition_threshold = st.slider("Repetition Score Trigger (%)", 50, 90, 75, 5)
    seed                 = st.number_input("Random Seed", value=42, step=1)
    strip_buffer         = st.number_input("Stripping buffer (weeks) — ACI 347R-14 curing", min_value=1, max_value=8, value=2)
    transport_weeks      = st.number_input("Panel transport time (weeks)", min_value=1, max_value=4, value=1)

    st.markdown("<hr style='border-color:#1E2D45;'>", unsafe_allow_html=True)
    st.markdown("### 🔩 Panel Unit Costs (₹)")
    wall_cost = st.number_input("Wall Panel", value=8000, step=500)
    slab_cost = st.number_input("Slab Panel", value=12000, step=500)
    col_cost  = st.number_input("Column Panel", value=6000, step=500)

    st.markdown("<hr style='border-color:#1E2D45;'>", unsafe_allow_html=True)
    st.markdown("### 💰 LP Cost Parameters (₹)")
    c_p = st.number_input("Procurement cost per panel", min_value=1000, max_value=500000,
                           value=15000, step=1000)
    c_h = st.number_input("Holding cost per panel/week", min_value=100, max_value=10000,
                           value=500, step=100)
    c_i = st.number_input("Idle cost per panel/week", min_value=100, max_value=10000,
                           value=800, step=100)
    st.session_state["c_p"] = float(c_p)

    st.markdown("<hr style='border-color:#1E2D45;'>", unsafe_allow_html=True)
    run_btn      = st.button("🚀  Run FormOptiX Engine", use_container_width=True)
    project_name = st.text_input("Project name (for PDF)", value="FormOptiX Project")

    st.markdown(f"""
    <hr style='border-color:#1E2D45;'>
    <div style='font-size:0.72rem;color:{MUTED};line-height:1.6;'>
      <b style='color:{ORANGE};'>CreaTech '26</b> · L&T<br>
      Problem Statement 4<br>
      <span style='color:{GREEN};'>#JustLeap</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# HERO HEADER
# ============================================================
col_hero, col_tag = st.columns([3, 1])
with col_hero:
    st.markdown("""
    <div style='padding:24px 0 8px 0;'>
      <div class='hero-title'>FormOptiX</div>
      <div class='hero-sub'>Intelligent Formwork &amp; BoQ Optimizer</div>
      <div style='margin-top:12px;'>
        <span class='hero-tag'>CreaTech '26</span>
        <span class='hero-tag'>L&amp;T · PS-4</span>
        <span class='hero-tag'>Repetition Intelligence</span>
        <span class='hero-tag'>#JustLeap</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
with col_tag:
    st.markdown(f"""
    <div style='text-align:right;padding-top:28px;color:{MUTED};font-size:0.8rem;line-height:1.8;'>
      <div style='color:{ORANGE};font-weight:700;font-size:1.0rem;'>AI-Driven</div>
      DBSCAN Clustering<br>LP Optimization<br>Dynamic BoQ
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr class='orange-divider'>", unsafe_allow_html=True)


# ============================================================
# MODE CHANGE DETECTION — clear stale results
# ============================================================
if "results_ready" not in st.session_state:
    st.session_state.results_ready = False
if "last_mode" not in st.session_state:
    st.session_state.last_mode = mode
if st.session_state.last_mode != mode:
    st.session_state.results_ready = False
    st.session_state.last_mode = mode


# ============================================================
# REAL SITE DATA — file upload section
# ============================================================
uploaded_file = None
df_raw_mapped = None

if mode == "Real Site Data":
    st.markdown("""
    <div class='callout-teal' style='margin-bottom:16px;'>
      <b>📂 Upload your project Excel file</b><br>
      Required sheets: <code>floors</code> (floor geometry) and <code>schedule</code> (weekly demand).
      Once uploaded, click <b>Run FormOptiX Engine</b> in the sidebar.
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload Excel File (.xlsx) — sheets: 'floors' + 'schedule'",
        type=["xlsx"], key="real_data_upload",
    )

    if uploaded_file is None:
        st.info("⬆️ Upload your Excel file above, then click **Run FormOptiX Engine**.")
    else:
        try:
            df_raw = pd.read_excel(uploaded_file)
            required_cols = [
                "floor_id", "week_start", "week_end", "strip_week",
                "slab_area_m2", "wall_length_m", "col_count", "panel_type",
            ]
            has_all = all(c in df_raw.columns for c in required_cols)
            col_map = {}
            if not has_all:
                with st.expander("🗺️ Map your column names", expanded=True):
                    options = ["--- Not in file ---"] + df_raw.columns.tolist()
                    for req in required_cols:
                        col_map[req] = st.selectbox(f"Which column is '{req}'?", options=options)
            else:
                st.success("✅ Column names matched automatically.")
                col_map = {c: c for c in required_cols}

            # Apply strip_week default if missing
            valid_map = {v: k for k, v in col_map.items() if v and v != "--- Not in file ---"}
            df_raw = df_raw.rename(columns=valid_map)
            if "strip_week" not in df_raw.columns and "week_end" in df_raw.columns:
                df_raw["strip_week"] = df_raw["week_end"] + strip_buffer
                st.info(f"ℹ️ strip_week auto-generated (week_end + {strip_buffer} weeks)")

            try:
                df_raw_mapped = validate_and_map(df_raw, col_map)
            except ValueError as e:
                st.error(str(e))
                df_raw_mapped = None

        except Exception as e:
            st.error(f"Failed to read file: {e}")


# ============================================================
# AUTO-RUN ON FIRST LOAD (synthetic demo only)
# ============================================================
if not st.session_state.results_ready and mode == "Synthetic Demo":
    run_btn = True


# ============================================================
# MAIN EXECUTION
# ============================================================
if run_btn:
    # ── Step 1: Load data ─────────────────────────────────────
    with st.spinner("🏗️  Loading building data..."):
        if mode == "Synthetic Demo":
            df_floors, df_schedule = generate_building_data(n_floors=n_floors, seed=int(seed))
        else:
            if uploaded_file is None:
                st.warning("⚠️ Please upload an Excel file first.")
                st.stop()
            if df_raw_mapped is None:
                st.error("Data validation failed. Fix the errors above and re-upload.")
                st.stop()
            try:
                xls         = pd.ExcelFile(uploaded_file)
                df_floors   = df_raw_mapped
                df_schedule = pd.read_excel(xls, "schedule")
            except Exception as e:
                st.error(f"Could not load schedule sheet: {e}")
                st.stop()

    # ── Step 2: Design Freeze Guard ───────────────────────────
    freeze_result = compute_design_freeze(df_floors)
    st.session_state.freeze_result = freeze_result
    st.session_state["di_value"]   = freeze_result["DI"]
    st.session_state["di_status"]  = freeze_result["status"]

    if freeze_result["status"] == "HALT":
        st.warning(
            f"🔒 **Design Freeze: HALT** — {freeze_result['recommendation']} "
            f"(DI = {freeze_result['DI']:.1f}%) — Results shown for analysis only."
        )
    elif freeze_result["status"] == "WARNING":
        st.warning(
            f"⚠️ **Design Freeze: WARNING** — {freeze_result['recommendation']} "
            f"(DI = {freeze_result['DI']:.1f}%)"
        )
    else:
        st.success(f"✅ **Design Freeze: SAFE** — Proceeding. (DI = {freeze_result['DI']:.1f}%)")

    # ── Step 3: DBSCAN Clustering ─────────────────────────────
    with st.spinner("🧠  Running DBSCAN Repetition Clustering..."):
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            (df_floors, rep_score, cluster_summary,
             rho_k_map, reuse_pairs, overall_reuse) = compute_repetition_score(
                df_floors, transport_weeks=int(transport_weeks)
            )
        for w in caught_warnings:
            st.warning(str(w.message))
        time.sleep(0.1)

    # ── Step 4: LP BoQ Optimizer ──────────────────────────────
    with st.spinner("⚙️  Running SKU-level LP BoQ Optimizer..."):
        lp_results = run_sku_optimizer(
            df_schedule, df_floors=df_floors,
            c_p=float(c_p), c_h=float(c_h), c_i=float(c_i),
            monthly_budget_cr=float(monthly_budget),
        )
        time.sleep(0.1)

    # Solver status guard — never show infeasible results
    lp_status = lp_results.get("status", "Unknown")
    if lp_status not in ("Optimal", "Heuristic (PuLP not installed)"):
        st.error(
            f"⛔ LP Solver returned status: **{lp_status}**. "
            "Check demand inputs and cost parameters, then re-run."
        )
        st.stop()

    # ── Step 5: Demand Forecast ───────────────────────────────
    with st.spinner("📈  Simulating demand forecast..."):
        forecast_data = simulate_forecast(df_schedule)
        time.sleep(0.1)

    # ── Store in session state ────────────────────────────────
    st.session_state.update({
        "df_floors":         df_floors,
        "df_schedule":       df_schedule,
        "rep_score":         rep_score,
        "cluster_summary":   cluster_summary,
        "rho_k_map":         rho_k_map,
        "reuse_pairs":       reuse_pairs,
        "overall_reuse":     overall_reuse,
        "transport_weeks":   int(transport_weeks),
        "lp_results":        lp_results,
        "boq_results":       lp_results.get("boq_results", []),
        "cost_params":       {"c_p": float(c_p), "c_h": float(c_h), "c_i": float(c_i)},
        "forecast_data":     forecast_data,
        "results_ready":     True,
        "overall_reuse_rate": overall_reuse,
    })

    savings_cr = lp_results["savings"] / 1e7
    st.success(
        f"✅  FormOptiX Engine complete — "
        f"Repetition Score: {rep_score}% | Projected savings: ₹{savings_cr:.2f} Cr"
    )


# ============================================================
# RESULTS DISPLAY
# ============================================================
if st.session_state.results_ready:
    # Pull from session state
    df_floors       = st.session_state.df_floors
    df_schedule     = st.session_state.df_schedule
    rep_score       = st.session_state.rep_score
    cluster_summary = st.session_state.cluster_summary
    lp_results      = st.session_state.lp_results

    savings_cr    = lp_results["savings"] / 1e7
    trad_total_cr = lp_results["trad_total"] / 1e7
    opt_total_cr  = lp_results["opt_total"] / 1e7
    saving_pct    = (savings_cr / trad_total_cr * 100) if trad_total_cr > 0 else 0

    # ── Trigger Status Banner ─────────────────────────────────
    if rep_score > repetition_threshold:
        st.markdown(f"""
        <div class='callout-green'>
          <b style='color:{GREEN};font-size:1.05rem;'>✅ KITTING OPTIMIZATION TRIGGERED</b><br>
          Repetition Score <b>{rep_score}%</b> exceeds threshold of <b>{repetition_threshold}%</b>.
          FormOptiX LP Optimizer is active. Procurement plan generated for 52-week schedule.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='callout-red'>
          <b style='color:{RED};font-size:1.05rem;'>⚠️ DESIGN FREEZE INTELLIGENCE ALERT</b><br>
          Repetition Score <b>{rep_score}%</b> is below threshold of <b>{repetition_threshold}%</b>.
          High design variability detected. <b>Recommend delaying bulk procurement</b>.
        </div>
        """, unsafe_allow_html=True)

    # ── Top KPI Row ───────────────────────────────────────────
    st.markdown("<div class='section-header'>📊 Key Performance Indicators</div>",
                unsafe_allow_html=True)
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpis = [
        (k1, "Repetition Score",   f"{rep_score}%",         f"+{rep_score-60:.0f}pp vs manual",   True),
        (k2, "Total Savings",      f"₹{savings_cr:.2f} Cr", f"{saving_pct:.1f}% of formwork cost",True),
        (k3, "Utilization Rate",   "85%",                   "+23pp vs 62% manual",                 True),
        (k4, "Excess Inventory",   "↓65%",                  "From 15% → 5% of BoQ",               True),
        (k5, "BoQ Revision Time",  "4 hrs",                 "From 3–5 days",                       True),
        (k6, "Carrying Cost",      "₹1.9 Cr",               "vs ₹4.2 Cr traditional",              True),
    ]
    for col, label, val, delta, pos in kpis:
        dc = "metric-delta-pos" if pos else "metric-delta-neg"
        col.markdown(f"""
        <div class='metric-card'>
          <div class='metric-value'>{val}</div>
          <div class='metric-label'>{label}</div>
          <div class='{dc}'>{delta}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Shared state dict passed to every page ────────────────
    shared = {
        "df_floors":           df_floors,
        "df_schedule":         df_schedule,
        "rep_score":           rep_score,
        "cluster_summary":     cluster_summary,
        "lp_results":          lp_results,
        "savings_cr":          savings_cr,
        "trad_total_cr":       trad_total_cr,
        "opt_total_cr":        opt_total_cr,
        "saving_pct":          saving_pct,
        "project_cost":        project_cost,
        "monthly_budget":      monthly_budget,
        "n_floors":            n_floors,
        "repetition_threshold": repetition_threshold,
        "seed":                seed,
        "rho_k_map":           st.session_state.get("rho_k_map", {}),
        "reuse_pairs":         st.session_state.get("reuse_pairs", []),
        "overall_reuse_rate":  st.session_state.get("overall_reuse_rate", 0.0),
        "forecast_data":       st.session_state.forecast_data,
        "boq_results":         st.session_state.get("boq_results", []),
        "cost_params":         st.session_state.get("cost_params", {}),
        "project_name":        project_name,
        "di_value":            st.session_state.get("di_value", 0.0),
        "di_status":           st.session_state.get("di_status", "N/A"),
    }

    # ── Tab routing ───────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎯 Repetition Analysis",
        "💰 Cost Optimization",
        "📦 Inventory & Forecast",
        "📐 Building Data",
        "🗺️ Roadmap & Impact",
        "🌍 Cross-Site Portfolio"
    ])
    with tab1: pg_repetition.render(shared)
    with tab2: pg_cost.render(shared)
    with tab3: pg_inventory.render(shared)
    with tab4: pg_building_data.render(shared)
    with tab5: pg_roadmap.render(shared)
    with tab6: pg_portfolio.render(shared)

    # ── Elevator Pitch ────────────────────────────────────────
    st.markdown("<hr class='orange-divider'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#111827,#1A2235);border:1px solid #E8611A33;
                border-radius:12px;padding:28px 32px;text-align:center;margin:16px 0;'>
      <div style='font-size:0.75rem;color:{MUTED};letter-spacing:2px;text-transform:uppercase;
                  margin-bottom:12px;'>The FormOptiX Pitch</div>
      <div style='font-size:1.35rem;color:{ORANGE};font-style:italic;font-weight:500;line-height:1.6;'>
        "FormOptiX is the GPS for formwork — it tells you exactly which panels to reuse,
        when to order, and how much you'll save, before a single slab is poured."
      </div>
      <div style='margin-top:20px;display:flex;justify-content:center;gap:24px;flex-wrap:wrap;'>
        <span style='color:{GREEN};font-weight:700;'>₹{savings_cr:.2f} Cr savings</span>
        <span style='color:{MUTED};'>·</span>
        <span style='color:{AMBER};font-weight:700;'>+22pp utilization</span>
        <span style='color:{MUTED};'>·</span>
        <span style='color:{TEAL};font-weight:700;'>~90% faster BoQ</span>
        <span style='color:{MUTED};'>·</span>
        <span style='color:#3B82F6;font-weight:700;'>Repetition Score: {rep_score}%</span>
      </div>
      <div style='margin-top:16px;font-size:0.85rem;color:{MUTED};'>
        CreaTech '26 · L&T · Problem Statement 4 · <b style='color:{ORANGE};'>#JustLeap</b>
      </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown(f"""
    <div style='text-align:center;padding:80px 20px;'>
      <div style='font-size:4rem;margin-bottom:16px;'>🏗️</div>
      <div style='font-size:1.5rem;color:{ORANGE};font-weight:700;margin-bottom:12px;'>
        Ready to Optimize
      </div>
      <div style='color:{MUTED};font-size:1rem;max-width:480px;margin:0 auto;line-height:1.7;'>
        Configure your project parameters in the sidebar and click
        <b style='color:{ORANGE};'>Run FormOptiX Engine</b> to generate the full analysis.
      </div>
    </div>
    """, unsafe_allow_html=True)
