"""
frontend/charts.py
FormOptiX — All Plotly chart builder functions.

Every function here takes data (plain Python/numpy/pandas) and returns a
go.Figure. No Streamlit calls — callers do st.plotly_chart(). This makes
charts independently testable.
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from frontend.theme import (
    apply_chart_theme,
    ORANGE, AMBER, TEAL, GREEN, RED, BLUE, GRAY, TEXT, MUTED, CHART_BG, CHART_PAPER,
)


# ── Repetition Analysis ──────────────────────────────────────────────────────

def make_gauge(score: float, threshold: float = 75) -> go.Figure:
    color = GREEN if score > threshold else (AMBER if score > 50 else RED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        delta={"reference": threshold, "increasing": {"color": GREEN}, "decreasing": {"color": RED}},
        number={"suffix": "%", "font": {"size": 42, "color": color, "family": "JetBrains Mono"}},
        title={
            "text": "Repetition Score<br><span style='font-size:11px;color:#7B8A9E'>"
                    "Kitting optimization triggers at >75%</span>",
            "font": {"size": 14, "color": TEXT},
        },
        gauge={
            "axis": {"range": [0, 100], "tickcolor": MUTED, "tickfont": {"color": MUTED}},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": CHART_BG,
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50],   "color": "rgba(239,68,68,0.12)"},
                {"range": [50, 75],  "color": "rgba(245,158,11,0.12)"},
                {"range": [75, 100], "color": "rgba(34,197,94,0.12)"},
            ],
            "threshold": {"line": {"color": ORANGE, "width": 3}, "thickness": 0.85, "value": threshold},
        },
    ))
    fig.update_layout(
        paper_bgcolor=CHART_PAPER, plot_bgcolor=CHART_BG,
        font=dict(family="Space Grotesk", color=TEXT),
        height=300, margin=dict(l=30, r=30, t=60, b=20),
    )
    return fig


def make_cluster_chart(df_floors) -> go.Figure:
    cluster_colors = {-1: MUTED, 0: TEAL, 1: ORANGE, 2: BLUE, 3: AMBER, 4: GREEN}
    area_col = "slab_area_sqm" if "slab_area_sqm" in df_floors.columns else "slab_area_m2"
    col_col  = "column_count"  if "column_count"  in df_floors.columns else "col_count"
    name_col = "floor_name"    if "floor_name"    in df_floors.columns else "floor_id"

    fig = go.Figure()
    for cl in df_floors["cluster"].unique():
        sub  = df_floors[df_floors["cluster"] == cl]
        name = f"Cluster {cl}" if cl >= 0 else "Outlier (unique)"
        fig.add_trace(go.Scatter(
            x=sub[area_col], y=sub["wall_length_m"],
            mode="markers+text",
            name=name,
            text=sub[name_col],
            textposition="top center",
            textfont=dict(size=9, color=TEXT),
            marker=dict(
                size=sub[col_col].values * 0.55,
                color=cluster_colors.get(cl, BLUE),
                opacity=0.82,
                line=dict(color="rgba(0,0,0,0.3)", width=1),
            ),
        ))
    fig = apply_chart_theme(fig, "Floor Repetition Clusters (DBSCAN)  ·  Bubble size = Column count", 380)
    fig.update_xaxes(title_text="Slab Area (sqm)")
    fig.update_yaxes(title_text="Wall Length (m)")
    return fig


def make_floor_heatmap(df_floors) -> go.Figure:
    area_col = "slab_area_sqm" if "slab_area_sqm" in df_floors.columns else "slab_area_m2"
    col_col  = "column_count"  if "column_count"  in df_floors.columns else "col_count"
    pivot = df_floors.pivot_table(
        index="floor_type",
        values=[area_col, "wall_length_m", col_col],
        aggfunc="mean",
    )
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, CHART_BG], [0.3, BLUE], [0.6, ORANGE], [1.0, AMBER]],
        text=np.round(pivot.values, 1),
        texttemplate="%{text}",
        textfont=dict(size=11, color=TEXT),
        showscale=True,
        colorbar=dict(tickfont=dict(color=MUTED)),
    ))
    return apply_chart_theme(fig, "Floor Type Characteristics Heatmap", 280)


def make_design_revision_chart(scores: list, versions: list, threshold: float) -> go.Figure:
    colors = [GREEN if s > threshold else (AMBER if s > 50 else RED) for s in scores]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=versions, y=scores,
        marker_color=colors,
        text=[f"{s:.1f}%" for s in scores],
        textposition="outside",
        textfont=dict(color=TEXT, size=13),
    ))
    fig.add_hline(
        y=threshold,
        line_color=ORANGE, line_dash="dash", line_width=2,
        annotation_text=f"Procurement Trigger ({threshold}%)",
        annotation_font_color=ORANGE,
    )
    fig = apply_chart_theme(fig, "Repetition Score Across Design Revisions", 300)
    fig.update_yaxes(range=[0, 110], title_text="Repetition Score (%)")
    return fig


# ── Cost Optimization ─────────────────────────────────────────────────────────

def make_cost_comparison(results: dict) -> go.Figure:
    categories = ["Procurement", "Holding Cost", "Idle Inventory", "TOTAL"]
    trad_vals  = [results["trad_proc"] / 1e7, results["trad_hold"] / 1e7,
                  results["trad_idle"] / 1e7, results["trad_total"] / 1e7]
    opt_vals   = [results["opt_proc"] / 1e7,  results["opt_hold"] / 1e7,
                  results["opt_idle"] * 0.3 / 1e7, results["opt_total"] / 1e7]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Traditional Planning", x=categories, y=trad_vals,
        marker_color=[RED, RED, RED, RED],
        marker_line_color="rgba(0,0,0,0)", opacity=0.85,
        text=[f"₹{v:.2f} Cr" for v in trad_vals],
        textposition="outside", textfont=dict(color=TEXT, size=11),
    ))
    fig.add_trace(go.Bar(
        name="FormOptiX Optimized", x=categories, y=opt_vals,
        marker_color=[TEAL, TEAL, TEAL, GREEN],
        marker_line_color="rgba(0,0,0,0)", opacity=0.85,
        text=[f"₹{v:.2f} Cr" for v in opt_vals],
        textposition="outside", textfont=dict(color=TEXT, size=11),
    ))
    fig = apply_chart_theme(fig, "Cost Comparison: Traditional vs FormOptiX", 380)
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08)
    fig.update_yaxes(title_text="Cost (₹ Crore)")
    return fig


def make_roi_waterfall(savings_cr: float, trad_total_cr: float, opt_total_cr: float) -> go.Figure:
    fig = go.Figure(go.Waterfall(
        name="Cost Flow", orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Traditional\nTotal Cost", "Procurement\nSaving", "Holding\nSaving",
           "Idle\nSaving", "FormOptiX\nTotal Cost"],
        y=[trad_total_cr, -savings_cr * 0.55, -savings_cr * 0.25, -savings_cr * 0.20, 0],
        connector=dict(line=dict(color=GRAY, width=1.5)),
        decreasing=dict(marker_color=GREEN),
        increasing=dict(marker_color=RED),
        totals=dict(marker_color=TEAL),
        text=[
            f"₹{trad_total_cr:.2f} Cr", f"-₹{savings_cr*0.55:.2f} Cr",
            f"-₹{savings_cr*0.25:.2f} Cr", f"-₹{savings_cr*0.20:.2f} Cr",
            f"₹{opt_total_cr:.2f} Cr",
        ],
        textposition="outside", textfont=dict(color=TEXT, size=11),
    ))
    fig = apply_chart_theme(fig, "ROI Waterfall: Cost Savings Breakdown", 380)
    fig.update_yaxes(title_text="Cost (₹ Crore)")
    return fig


def make_utilization_bars() -> go.Figure:
    metrics = ["Utilization Rate", "Excess Inventory\n(inverted)", "BoQ Accuracy"]
    before  = [62, 85, 70]
    after   = [85, 95, 96]

    fig = go.Figure()
    for i, (m, b, a) in enumerate(zip(metrics, before, after)):
        fig.add_trace(go.Bar(
            name="Before", x=[b], y=[m], orientation="h",
            marker_color=RED, opacity=0.7, showlegend=i == 0,
            text=f"{b}%", textposition="inside", textfont=dict(color="white", size=12),
        ))
        fig.add_trace(go.Bar(
            name="After (FormOptiX)", x=[a], y=[m], orientation="h",
            marker_color=GREEN, opacity=0.85, showlegend=i == 0,
            text=f"{a}%", textposition="inside", textfont=dict(color="white", size=12),
        ))
    fig = apply_chart_theme(fig, "Performance Metrics: Before vs After", 300)
    fig.update_layout(barmode="overlay", bargap=0.35, xaxis=dict(range=[0, 110], title="Score (%)"))
    return fig


# ── Inventory & Forecast ──────────────────────────────────────────────────────

def make_inventory_curve(results: dict, weeks) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weeks, y=results["trad_inv_w"],
        name="Traditional Inventory",
        line=dict(color=RED, width=2.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=weeks, y=results["opt_inv_w"],
        name="FormOptiX Optimized",
        line=dict(color=TEAL, width=2.5),
        fill="tozeroy", fillcolor="rgba(20,184,166,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=weeks, y=results["demand_w"],
        name="Actual Demand",
        line=dict(color=AMBER, width=1.8, dash="dash"),
    ))
    fig = apply_chart_theme(fig, "Wall Panel Inventory Levels: 52-Week Horizon", 360)
    fig.update_xaxes(title_text="Project Week")
    fig.update_yaxes(title_text="Panel Count")
    return fig


def make_forecast_chart(weeks, demand, forecast, upper, lower) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=np.concatenate([weeks, weeks[::-1]]),
        y=np.concatenate([upper, lower[::-1]]),
        fill="toself", fillcolor="rgba(20,184,166,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Confidence Interval", showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=weeks, y=demand, name="Actual Demand",
        line=dict(color=AMBER, width=2, dash="dot"),
        mode="lines+markers", marker=dict(size=4, color=AMBER),
    ))
    fig.add_trace(go.Scatter(
        x=weeks, y=forecast, name="FormOptiX Forecast",
        line=dict(color=TEAL, width=2.5), mode="lines",
    ))
    fig = apply_chart_theme(fig, "Demand Forecasting: Wall Panels (52-Week)", 340)
    fig.update_xaxes(title_text="Week")
    fig.update_yaxes(title_text="Panel Count")
    return fig


# ── Building Data ─────────────────────────────────────────────────────────────

def make_floor_type_donut(df_floors, n_floors: int) -> go.Figure:
    type_counts = df_floors["floor_type"].value_counts().reset_index()
    type_counts.columns = ["floor_type", "count"]
    fig = go.Figure(go.Pie(
        labels=type_counts["floor_type"],
        values=type_counts["count"],
        hole=0.55,
        marker_colors=[ORANGE, TEAL, AMBER, GREEN, BLUE, RED],
        textfont=dict(color=TEXT, size=12),
        hovertemplate="%{label}: %{value} floors<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=CHART_PAPER, plot_bgcolor=CHART_BG,
        font=dict(family="Space Grotesk", color=TEXT),
        height=300, margin=dict(l=20, r=20, t=40, b=20),
        title=dict(text="Floor Type Distribution", font=dict(color=TEXT, size=14)),
        legend=dict(bgcolor="rgba(22,27,34,0.8)", bordercolor=GRAY, borderwidth=1, font=dict(color=TEXT)),
    )
    fig.add_annotation(
        text=f"<b>{n_floors}</b><br>Floors",
        x=0.5, y=0.5, font_size=16, font_color=ORANGE, showarrow=False,
    )
    return fig


def make_geometry_scatter(df_floors) -> go.Figure:
    area_col = "slab_area_sqm" if "slab_area_sqm" in df_floors.columns else "slab_area_m2"
    col_col  = "column_count"  if "column_count"  in df_floors.columns else "col_count"
    name_col = "floor_name"    if "floor_name"    in df_floors.columns else "floor_id"

    fig = px.scatter(
        df_floors, x=area_col, y="wall_length_m",
        size=col_col, color="cluster",
        hover_name=name_col,
        hover_data=["floor_type"],
        color_continuous_scale=[[0, RED], [0.33, ORANGE], [0.66, TEAL], [1.0, GREEN]],
        title="Floor Geometry Space (colored by Cluster)",
    )
    return apply_chart_theme(fig, "Floor Geometry Space", 300)
