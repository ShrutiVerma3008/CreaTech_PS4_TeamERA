"""
frontend/theme.py
FormOptiX — CSS injection, color tokens, chart theme helper.

Import this first in app.py before any other frontend modules.
"""

import streamlit as st
import plotly.graph_objects as go


# ── Color tokens ─────────────────────────────────────────────
BG               = "#0A0E1A"
BG_SIDEBAR_START = "#0F1525"
BG_SIDEBAR_END   = "#0A0E1A"
TEXT             = "#E8EDF5"
MUTED            = "#7B8A9E"
CARD_START       = "#111827"
CARD_END         = "#1A2235"
BORDER           = "#1E2D45"
ORANGE           = "#E8611A"   # L&T signature orange
GREEN            = "#22C55E"
RED              = "#EF4444"
TEAL             = "#14B8A6"
BLUE             = "#3B82F6"
AMBER            = "#F59E0B"
CHART_BG         = "#111827"
CHART_PAPER      = "#0A0E1A"
GRAY             = "#1E2D45"
INPUT_BG         = "#111827"


def inject_css() -> None:
    """Inject the global FormOptiX dark theme CSS into the Streamlit app."""
    st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Space Grotesk', sans-serif;
    background-color: {BG};
    color: {TEXT};
  }}
  .stApp {{ background: {BG}; }}

  [data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {BG_SIDEBAR_START} 0%, {BG_SIDEBAR_END} 100%);
    border-right: 1px solid {BORDER};
  }}
  [data-testid="stSidebar"] .stMarkdown h1,
  [data-testid="stSidebar"] .stMarkdown h2,
  [data-testid="stSidebar"] .stMarkdown h3 {{ color: {ORANGE}; }}

  .metric-card {{
    background: linear-gradient(135deg, {CARD_START} 0%, {CARD_END} 100%);
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 20px 24px;
    margin: 6px 0;
    transition: border-color 0.2s;
  }}
  .metric-card:hover {{ border-color: {ORANGE}; }}
  .metric-value {{
    font-size: 2.2rem;
    font-weight: 700;
    color: {ORANGE};
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.1;
  }}
  .metric-label {{
    font-size: 0.78rem;
    color: {MUTED};
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
  }}
  .metric-delta-pos {{ color: {GREEN}; font-size: 0.85rem; font-weight: 600; }}
  .metric-delta-neg {{ color: {RED};   font-size: 0.85rem; font-weight: 600; }}

  .section-header {{
    background: linear-gradient(90deg, {ORANGE} 0%, transparent 100%);
    padding: 10px 20px;
    border-radius: 6px;
    margin: 24px 0 16px 0;
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: {TEXT} !important;
  }}

  .callout-orange {{
    background: rgba(232,97,26,0.12);
    border-left: 4px solid {ORANGE};
    border-radius: 0 8px 8px 0;
    padding: 14px 18px; margin: 12px 0;
  }}
  .callout-green {{
    background: rgba(34,197,94,0.10);
    border-left: 4px solid {GREEN};
    border-radius: 0 8px 8px 0;
    padding: 14px 18px; margin: 12px 0;
  }}
  .callout-red {{
    background: rgba(239,68,68,0.10);
    border-left: 4px solid {RED};
    border-radius: 0 8px 8px 0;
    padding: 14px 18px; margin: 12px 0;
  }}
  .callout-teal {{
    background: rgba(20,184,166,0.10);
    border-left: 4px solid {TEAL};
    border-radius: 0 8px 8px 0;
    padding: 14px 18px; margin: 12px 0;
  }}

  .hero-title {{
    font-size: 3rem; font-weight: 700;
    background: linear-gradient(135deg, {ORANGE} 0%, {AMBER} 60%, {TEXT} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px; line-height: 1.05;
  }}
  .hero-sub {{ color: {MUTED}; font-size: 1rem; letter-spacing: 2px; text-transform: uppercase; margin-top: 6px; }}
  .hero-tag {{
    display: inline-block;
    background: rgba(232,97,26,0.15);
    border: 1px solid {ORANGE};
    color: {ORANGE};
    padding: 3px 12px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600;
    letter-spacing: 1px; margin-right: 8px; margin-top: 12px;
  }}

  .custom-table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; margin: 12px 0; }}
  .custom-table th {{
    background: #1A2235; color: {ORANGE};
    padding: 10px 14px; text-align: left;
    font-weight: 600; letter-spacing: 0.5px;
    border-bottom: 2px solid {ORANGE};
  }}
  .custom-table td {{ padding: 9px 14px; border-bottom: 1px solid {BORDER}; color: {TEXT}; }}
  .custom-table tr:nth-child(even) td {{ background: #111827; }}
  .custom-table tr:hover td {{ background: rgba(232,97,26,0.06); }}
  .td-green {{ color: {GREEN} !important; font-weight: 600; }}
  .td-orange {{ color: {ORANGE} !important; font-weight: 700; }}

  .phase-badge {{
    display: inline-block; padding: 4px 14px;
    border-radius: 20px; font-size: 0.75rem;
    font-weight: 700; letter-spacing: 0.5px; margin: 3px 2px;
  }}
  .phase-0 {{ background: rgba(20,184,166,0.2); color: {TEAL}; border: 1px solid {TEAL}; }}
  .phase-1 {{ background: rgba(232,97,26,0.2); color: {ORANGE}; border: 1px solid {ORANGE}; }}
  .phase-2 {{ background: rgba(59,130,246,0.2); color: {BLUE}; border: 1px solid {BLUE}; }}
  .phase-3 {{ background: rgba(245,158,11,0.2); color: {AMBER}; border: 1px solid {AMBER}; }}

  .orange-divider {{
    height: 2px;
    background: linear-gradient(90deg, {ORANGE}, transparent);
    border: none; margin: 20px 0;
  }}

  .stSlider > div > div > div > div {{ background: {ORANGE} !important; }}
  .stSelectbox > div > div {{ background: {INPUT_BG}; border-color: {BORDER}; }}
  .stNumberInput > div > div > input {{ background: {INPUT_BG}; border-color: {BORDER}; color: {TEXT}; }}
  div[data-testid="stMetric"] {{
    background: {CARD_START}; border: 1px solid {BORDER};
    border-radius: 10px; padding: 14px;
  }}
  div[data-testid="stMetric"] label {{ color: {MUTED} !important; }}
  div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: {ORANGE} !important; font-family: 'JetBrains Mono', monospace;
  }}
  .stButton > button {{
    background: linear-gradient(135deg, {ORANGE}, {AMBER});
    color: white; border: none; border-radius: 8px;
    font-weight: 700; letter-spacing: 0.5px;
    padding: 10px 28px; transition: opacity 0.2s;
  }}
  .stButton > button:hover {{ opacity: 0.85; }}
  h1, h2, h3 {{ color: {TEXT} !important; }}
  .stTabs [data-baseweb="tab"] {{ color: {MUTED}; }}
  .stTabs [aria-selected="true"] {{ color: {ORANGE} !important; border-bottom-color: {ORANGE} !important; }}
</style>
""", unsafe_allow_html=True)


def apply_chart_theme(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    """Apply the FormOptiX dark theme to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor=CHART_PAPER,
        plot_bgcolor=CHART_BG,
        font=dict(family="Space Grotesk", color=TEXT, size=12),
        title=dict(
            text=title,
            font=dict(color=TEXT, size=15, family="Space Grotesk"),
            x=0.02, xanchor="left",
        ),
        height=height,
        margin=dict(l=50, r=30, t=50, b=50),
        legend=dict(
            bgcolor="rgba(22,27,34,0.8)",
            bordercolor=GRAY,
            borderwidth=1,
            font=dict(color=TEXT),
        ),
        xaxis=dict(gridcolor=GRAY, linecolor=GRAY, tickfont=dict(color=MUTED), zerolinecolor=GRAY),
        yaxis=dict(gridcolor=GRAY, linecolor=GRAY, tickfont=dict(color=MUTED), zerolinecolor=GRAY),
    )
    return fig
