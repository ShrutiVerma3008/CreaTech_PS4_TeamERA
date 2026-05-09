"""
Surgical fix: replaces the broken what-if slider block (lines 2588-2635)
with a correct version, and inserts the sensitivity expander right after.
Run from try1/ directory.
"""
import sys, re
sys.stdout.reconfigure(encoding="utf-8")

TARGET = r"d:\sem_6\creaTech\try1\try2_real.py"

with open(TARGET, encoding="utf-8") as f:
    lines = f.readlines()

# Locate the broken block
START_MARKER = '        change_pct = st.slider(\n'
END_MARKER   = '        # ─' + '─ SKU-level BoQ breakdown table'

start_idx = None
end_idx   = None
for i, line in enumerate(lines):
    if line == START_MARKER and start_idx is None:
        start_idx = i
    if start_idx is not None and i > start_idx and '# ── SKU-level BoQ breakdown table' in line:
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"FAIL: markers not found. start={start_idx} end={end_idx}")
    sys.exit(1)

print(f"Replacing lines {start_idx+1}–{end_idx+1}")

REPLACEMENT = '''\
        change_pct = st.slider(
            "Design change magnitude (%)",
            min_value=0, max_value=30, value=0, step=5,
            key="whatif_slider",
            help="Simulates increasing week_cost and procure qty "
                 "by this % for a random subset of procurement rows "
                 "(Ibbs, 1997: scope change impact on procurement)."
        )

        if change_pct > 0:
            import copy as _copy, random as _random
            boq_base_sim = st.session_state.get("boq_results", [])

            if boq_base_sim:
                _random.seed(42)
                boq_sim  = _copy.deepcopy(boq_base_sim)
                affected = _random.sample(
                    range(len(boq_sim)),
                    k=max(1, int(len(boq_sim) * 0.30))
                )
                for _idx in affected:
                    boq_sim[_idx]["week_cost"] = round(
                        boq_sim[_idx]["week_cost"] * (1 + change_pct / 100)
                    )
                    boq_sim[_idx]["procure"] = round(
                        boq_sim[_idx]["procure"] * (1 + change_pct / 100)
                    )
                sim_total      = sum(r["week_cost"] for r in boq_sim)
                base_total_sim = sum(r["week_cost"] for r in boq_base_sim)
                delta          = sim_total - base_total_sim
                _w_col1, _w_col2, _w_col3 = st.columns(3)
                _w_col1.metric("Base optimized cost",
                               f"Rs {base_total_sim / 1e7:.2f} Cr")
                _w_col2.metric(f"Cost with {change_pct}% design change",
                               f"Rs {sim_total / 1e7:.2f} Cr",
                               delta=f"+Rs {delta / 1e7:.2f} Cr",
                               delta_color="inverse")
                _w_col3.metric("Additional cost of change",
                               f"Rs {delta / 1e7:.2f} Cr",
                               help="Ibbs (1997): design changes cause "
                                    "non-linear procurement overrun.")
                st.caption(
                    f"Simulation: {change_pct}% cost increase "
                    f"applied to {len(affected)} of {len(boq_sim)} "
                    f"procurement rows (30% of rows, seed=42 for reproducibility)."
                )
            else:
                st.info("Run the FormOptiX engine first to enable what-if simulation.")

        # ── Savings sensitivity analysis expander ─────────────────────────────
        # Hillier & Lieberman (2021) OR sensitivity validation methodology.
        with st.expander("\\U0001f4ca Savings sensitivity analysis", expanded=False):
            _s_opt  = float(lp_results.get("optimized_total",
                            lp_results.get("opt_total", optimized_total)))
            _s_base = float(baseline_total)
            _s_pct  = float(saving_pct)
            _sens_rows = compute_sensitivity_table(_s_opt, _s_base, _s_pct)

            if _sens_rows:
                _sens_df = pd.DataFrame(_sens_rows).rename(columns={
                    "scenario":        "Scenario",
                    "adj_baseline":    "Baseline (Cr)",
                    "adj_optimized":   "Optimized (Cr)",
                    "adj_savings":     "Savings (Cr)",
                    "adj_savings_pct": "Savings %",
                })

                def _highlight_sens(col):
                    if col.name != "Savings %":
                        return ["" for _ in col]
                    _cmax = col.max()
                    _cmin = col.min()
                    return [
                        "background-color:#1a3a2a; color:#4ade80;" if v == _cmax
                        else "background-color:#3a2a00; color:#f59e0b;" if v == _cmin
                        else ""
                        for v in col
                    ]

                _styled_sens = (
                    _sens_df.style
                    .apply(_highlight_sens, axis=0)
                    .format({
                        "Baseline (Cr)":  "{:.2f}",
                        "Optimized (Cr)": "{:.2f}",
                        "Savings (Cr)":   "{:.2f}",
                        "Savings %":      "{:.1f}%",
                    })
                )
                st.dataframe(_styled_sens, use_container_width=True, hide_index=True)

                _best_pct  = max(r["adj_savings_pct"] for r in _sens_rows)
                _worst_pct = min(r["adj_savings_pct"] for r in _sens_rows)
                _sc1, _sc2, _sc3 = st.columns(3)
                _sc1.metric("Best case savings",  f"{_best_pct:.1f}%")
                _sc2.metric("Worst case savings", f"{_worst_pct:.1f}%")
                _sc3.metric("Savings range",      f"{_worst_pct:.1f}%\\u2013{_best_pct:.1f}%")
                st.caption(
                    "Sensitivity validated per Hillier & Lieberman (2021) OR methodology. "
                    f"Savings range: {_worst_pct:.1f}%\\u2013{_best_pct:.1f}% "
                    "across cost, schedule, and redesign scenarios. "
                    "Full field calibration: Phase 2 (real-site procurement records)."
                )
            else:
                st.info("Run the FormOptiX engine to compute sensitivity analysis.")

        # ── SKU-level BoQ breakdown table (Step 6) ──────────────────────────
'''

new_lines = lines[:start_idx] + [REPLACEMENT] + lines[end_idx:]

with open(TARGET, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"Done. File now has {len(new_lines)} lines.")
