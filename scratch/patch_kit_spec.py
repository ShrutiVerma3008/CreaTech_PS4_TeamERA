"""
scratch/patch_kit_spec.py
Replaces the old single-type Kit Specification block in try2_real.py
with the new multi-type IS 1200 version (lines 2192-2252).
"""
import sys

TARGET = "try2_real.py"
START_LINE = 2192  # 1-indexed, inclusive
END_LINE   = 2252  # 1-indexed, inclusive

NEW_BLOCK = '''        # -- Kit Specification v2: per-cluster, multi-type IS 1200 table ---
        # Gap 1 v2: compute_kit_specification uses actual formwork areas
        # (slab, column, beam, staircase) per IS 1200 Part 1 (1992).
        # Hanna (1998) Ch.4; Peurifoy & Oberlender (2010) Ch.7.
        if kit_families:
            _coverage_ratios = {
                "slab":  st.session_state.get("coverage_slab",  1.2),
                "col":   st.session_state.get("coverage_col",   0.9),
                "beam":  st.session_state.get("coverage_beam",  0.6),
                "stair": st.session_state.get("coverage_stair", 0.5),
            }
            _df_for_kit = st.session_state.get(
                "df_floors_is456",
                st.session_state.get("df_floors", pd.DataFrame())
            )

            _cluster_ids = (
                sorted([c for c in _df_for_kit["cluster"].unique() if c != -1])
                if "cluster" in _df_for_kit.columns else []
            )

            if _cluster_ids:
                for _cid in _cluster_ids:
                    _cdf = _df_for_kit[_df_for_kit["cluster"] == _cid]
                    _kit = compute_kit_specification(_cdf, _coverage_ratios)
                    if not _kit:
                        continue
                    with st.expander(
                        f"\U0001f4d0 Kit Specification \u2014 Cluster {_cid} "
                        f"({len(_cdf)} floors)",
                        expanded=True,
                    ):
                        _kit_df = pd.DataFrame(_kit)

                        def _hl_max(col):
                            if col.name == "Panels Required":
                                max_v = col.max()
                                return [
                                    "background-color: #FEF3C7"
                                    if v == max_v else ""
                                    for v in col
                                ]
                            return [""] * len(col)

                        try:
                            st.dataframe(
                                _kit_df.style.apply(_hl_max),
                                use_container_width=True,
                                hide_index=True,
                            )
                        except Exception:
                            st.dataframe(_kit_df, use_container_width=True, hide_index=True)

                        _total_panels = _kit_df["Panels Required"].sum()
                        st.metric(
                            "Total Panels This Kit",
                            f"{_total_panels:,}",
                            help="Sum across all formwork types + 10% buffer",
                        )
                        st.caption(
                            "Coverage ratios adjustable in sidebar. "
                            "IS 1200 Part 1 (1992) line item refs shown. "
                            "10% buffer applied per standard site practice. "
                            "Source: Hanna (1998) Ch.4, "
                            "Peurifoy & Oberlender (2010) Ch.7."
                        )
            else:
                # Fallback: old generate_kit_specification display
                _df_for_spec = st.session_state.get("df_floors_is456", None)
                if _df_for_spec is None:
                    _df_for_spec = st.session_state.get(
                        "df_floors", pd.DataFrame(columns=["floor_id", "slab_area_sqm"])
                    )
                with st.expander("\U0001f4d0 Kit Specification \u2014 Panel Counts", expanded=False):
                    st.caption(
                        "Panel counts derived from avg. slab area / SKU coverage ratio. "
                        "Buffer = 10% of panel_count, rounded up. "
                        "Source: Peurifoy & Oberlender (2010) Ch.7."
                    )
                    _kit_spec_df = generate_kit_specification(
                        kit_families=kit_families, df=_df_for_spec, sku_coverage_ratios=None
                    )
                    if not _kit_spec_df.empty:
                        st.dataframe(_kit_spec_df, use_container_width=True, hide_index=True)

            # Noise cluster (atypical floors)
            if "cluster" in _df_for_kit.columns and (-1 in _df_for_kit["cluster"].values):
                _noise_df = _df_for_kit[_df_for_kit["cluster"] == -1]
                with st.expander(
                    f"\U0001f536 Atypical Floors \u2014 Custom Order Required "
                    f"({len(_noise_df)} floors)"
                ):
                    st.warning(
                        f"{len(_noise_df)} floor(s) do not fit any standard kit family. "
                        "These require custom panel orders. "
                        f"Floors: {_noise_df['floor_id'].tolist()}"
                    )
                    _noise_kit = compute_kit_specification(_noise_df, _coverage_ratios)
                    if _noise_kit:
                        st.dataframe(
                            pd.DataFrame(_noise_kit),
                            use_container_width=True,
                            hide_index=True,
                        )

'''

with open(TARGET, "r", encoding="utf-8") as f:
    lines = f.readlines()

total = len(lines)
assert START_LINE <= END_LINE <= total, f"Line range {START_LINE}-{END_LINE} out of bounds ({total})"

# Build new content
new_lines = lines[:START_LINE - 1] + [NEW_BLOCK] + lines[END_LINE:]

with open(TARGET, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"Patched {TARGET}: replaced lines {START_LINE}-{END_LINE} ({END_LINE-START_LINE+1} lines) with new kit spec block.")
print(f"New file: {len(new_lines)} logical entries (+ 1 block)")
