"""
frontend/pages/roadmap.py
Tab 5 — Roadmap & Impact: phase cards, impact table, novelty features, competitive landscape.
"""

import streamlit as st
from frontend.theme import ORANGE, TEAL, BLUE, AMBER


def render(state: dict) -> None:
    rep_score    = state["rep_score"]
    savings_cr   = state["savings_cr"]
    saving_pct   = state["saving_pct"]

    # ── Implementation Roadmap ────────────────────────────────────────────
    st.markdown("<div class='section-header'>🗺️ Implementation Roadmap</div>",
                unsafe_allow_html=True)

    phases = [
        ("Phase 0", "0–3 Months",  "Prototype", "0D9488",
         ["Python prototype on synthetic data", "DBSCAN + LP + Prophet modules",
          "Cost dashboard (this app)"],
         "Repetition Score algo validated on 3 test buildings"),
        ("Phase 1", "3–9 Months",  "Pilot",     "E8611A",
         ["Single L&T residential tower", "BIM integration (Revit plugin)",
          "L&T historical data as training"],
         "≥12% formwork cost reduction demonstrated"),
        ("Phase 2", "9–18 Months", "Scale",     "388BFD",
         ["10 projects + ERP + Primavera integration", "RFID panel digital twin rollout",
          "Cross-project sharing engine"],
         "₹15–20 Cr cumulative savings"),
        ("Phase 3", "18–36 Months","Platform",  "F5A623",
         ["SaaS for external contractors", "Anonymised project templates",
          "Per-project pricing"],
         "Onboard 3 builders; ARR target ₹5 Cr"),
    ]
    cols = st.columns(4)
    for col, (tag, time_r, title, color, items, kpi) in zip(cols, phases):
        items_html = "".join([f"<li style='margin:5px 0;color:#C9D1D9;'>{it}</li>" for it in items])
        col.markdown(f"""
        <div style='background:#111827;border:1px solid #1E2D45;border-radius:12px;
                    border-top:4px solid #{color};padding:16px;height:340px;'>
          <div style='color:#{color};font-weight:700;font-size:0.78rem;letter-spacing:1px;'>{tag}</div>
          <div style='color:#7B8A9E;font-size:0.75rem;'>{time_r}</div>
          <div style='color:#E8EDF5;font-weight:700;font-size:1.1rem;margin:8px 0;'>{title}</div>
          <ul style='padding-left:16px;font-size:0.82rem;margin:0;'>{items_html}</ul>
          <div style='margin-top:12px;background:rgba(255,255,255,0.05);
                      border-radius:6px;padding:8px;font-size:0.78rem;color:#{color};font-weight:600;'>
            ✓ {kpi}
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Impact Summary ────────────────────────────────────────────────────
    st.markdown("<br><div class='section-header'>📊 Full Impact Summary</div>",
                unsafe_allow_html=True)
    st.markdown(f"""
    <table class='custom-table'>
      <tr><th>Metric</th><th>Before (Manual)</th><th>After (FormOptiX)</th><th>Improvement</th></tr>
      <tr><td>Formwork Utilization Rate</td><td>60–65%</td>
          <td class='td-green'>82–87%</td><td class='td-green'>+22 percentage points</td></tr>
      <tr><td>BoQ Revision Cycle Time</td><td>3–5 days</td>
          <td class='td-green'>&lt;4 hours</td><td class='td-green'>~90% faster</td></tr>
      <tr><td>Excess Inventory (% of BoQ)</td><td>12–18%</td>
          <td class='td-green'>4–6%</td><td class='td-green'>~65% reduction</td></tr>
      <tr><td>Carrying Cost (₹500 Cr project)</td><td>₹3–5 Cr</td>
          <td class='td-green'>₹1.5–2 Cr</td><td class='td-green'>~55% lower</td></tr>
      <tr><td>Repetition Score (measured)</td><td>Not tracked</td>
          <td class='td-orange'>{rep_score}%</td><td class='td-green'>New KPI created</td></tr>
      <tr><td><b>Total Formwork Cost Saving</b></td><td><b>Baseline</b></td>
          <td class='td-green'><b>₹{savings_cr:.2f} Cr</b></td>
          <td class='td-green'><b>{saving_pct:.1f}% reduction</b></td></tr>
    </table>
    """, unsafe_allow_html=True)

    # ── Novelty Features ──────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🆕 Novelty Features</div>", unsafe_allow_html=True)
    n1, n2, n3 = st.columns(3)
    novelties = [
        (n1, "🔒 Design Freeze Intelligence", TEAL,
         "Monitors BIM version history. Flags if Repetition Score drops >15% between design "
         "iterations. Delays procurement until design stability threshold is reached."),
        (n2, "📡 Panel Digital Twin", ORANGE,
         "QR/RFID code per panel tracks deployment, removal, inspection cycles in real-time. "
         "Predictive maintenance: 'Batch F-240 due for inspection after next use.'"),
        (n3, "🔗 Cross-Project Sharing Engine", BLUE,
         "Identifies idle panels at Site A that match demand at Site B. "
         "Inter-project reallocation reduces rental costs across the portfolio."),
    ]
    for col, title, color, desc in novelties:
        col.markdown(f"""
        <div style='background:#111827;border-left:4px solid {color};border-radius:8px;padding:16px;'>
          <div style='font-weight:700;color:{color};font-size:1.0rem;margin-bottom:10px;'>{title}</div>
          <div style='font-size:0.84rem;color:#C9D1D9;line-height:1.6;'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Competitive Landscape ─────────────────────────────────────────────
    st.markdown("<br><div class='section-header'>⚔️ Competitive Landscape</div>",
                unsafe_allow_html=True)
    st.markdown("""
    <table class='custom-table'>
      <tr><th>Tool</th><th>Scheduling</th><th>Procurement</th><th>Design</th>
          <th>Repetition Intelligence</th><th>Cross-Project</th><th>Digital Twin</th></tr>
      <tr><td>Primavera P6</td>
        <td style='color:#22C55E;'>✓</td><td style='color:#EF4444;'>✗</td><td style='color:#EF4444;'>✗</td>
        <td style='color:#EF4444;'>✗</td><td style='color:#EF4444;'>✗</td><td style='color:#EF4444;'>✗</td></tr>
      <tr><td>SAP ERP</td>
        <td style='color:#EF4444;'>✗</td><td style='color:#22C55E;'>✓</td><td style='color:#EF4444;'>✗</td>
        <td style='color:#EF4444;'>✗</td><td style='color:#EF4444;'>✗</td><td style='color:#EF4444;'>✗</td></tr>
      <tr><td>BIM (Revit)</td>
        <td style='color:#EF4444;'>✗</td><td style='color:#EF4444;'>✗</td><td style='color:#22C55E;'>✓</td>
        <td style='color:#EF4444;'>✗</td><td style='color:#EF4444;'>✗</td><td style='color:#EF4444;'>✗</td></tr>
      <tr style='background:rgba(232,97,26,0.08);'>
        <td class='td-orange'><b>FormOptiX ★</b></td>
        <td style='color:#22C55E;'><b>✓</b></td><td style='color:#22C55E;'><b>✓</b></td>
        <td style='color:#22C55E;'><b>✓</b></td><td style='color:#22C55E;'><b>✓</b></td>
        <td style='color:#22C55E;'><b>✓</b></td><td style='color:#22C55E;'><b>✓</b></td></tr>
    </table>
    """, unsafe_allow_html=True)
