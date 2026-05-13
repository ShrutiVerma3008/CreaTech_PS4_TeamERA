import pandas as pd
import streamlit as st

# ==============================================================
# Stripping time helpers
# ==============================================================

# IS 456:2000 Clause 11.3 — Stripping time for Indian RCC construction.
# Primary standard for L&T and all Indian contractors.
# BIS (2000). IS 456:2000 Plain and Reinforced Concrete — Code of Practice,
#   Clause 11.3, Table 11. Bureau of Indian Standards.
# SKU-based mapping derived from formwork type classification.
# Hanna (1998) Ch.4: stripping time directly controls panel reuse
#   eligibility window; incorrect strip_week delays reuse and inflates cost.

SKU_STRIP_WEEKS_IS456 = {
    # IS 456:2000 Cl.11.3: 14 days (slab > 4.5m span) = 2 weeks
    "ALU-600":  2,
    # IS 456:2000 Cl.11.3: 7 days (slab ≤ 4.5m / props left under) = 1 week
    "ALU-450":  1,
    # IS 456:2000 Cl.11.3: 14 days (beam soffits, span ≤ 6m) = 2 weeks
    "H20-beam": 2,
}
DEFAULT_STRIP_WEEKS_IS456 = 2  # conservative default for unknown SKUs


def get_strip_weeks_is456(df: pd.DataFrame) -> "pd.Series":
    """
    Return per-row strip week delta based on IS 456:2000 Clause 11.3.

    Uses the 'sku' or 'panel_type' column (whichever is present) to look up
    the minimum stripping time for each panel type.

    Returns
    -------
    pd.Series of int — strip_week delta (weeks after week_end)

    Academic basis
    --------------
    IS 456:2000 Cl.11.3 (BIS): Indian mandatory standard for RCC
      stripping time. Primary reference for all L&T projects.
    Hanna (1998) Ch.4: stripping time controls panel reuse window.
    """
    # Accept either 'sku' or 'panel_type' column
    sku_col = "sku" if "sku" in df.columns else "panel_type"
    if sku_col not in df.columns:
        return pd.Series([DEFAULT_STRIP_WEEKS_IS456] * len(df), index=df.index)

    return (
        df[sku_col]
        .map(SKU_STRIP_WEEKS_IS456)
        .fillna(DEFAULT_STRIP_WEEKS_IS456)
        .astype(int)
    )


def get_strip_weeks_aci(df: pd.DataFrame) -> "pd.Series":
    """
    Return per-row strip week delta based on ACI 347R-14 Section 5.

    Flat 2-week buffer regardless of SKU or span.
    Kept as secondary reference for international project comparison.

    Returns
    -------
    pd.Series of int — constant 2 for every row

    Academic basis
    --------------
    ACI Committee 347 (2014). ACI 347R-14: Guide to Formwork for Concrete.
      Section 5 — minimum cure time before stripping.
    """
    return pd.Series([2] * len(df), index=df.index)


def validate_and_map(df, col_map, stripping_standard: str = "IS456"):
    """
    Validate, rename, and enrich a floor DataFrame.

    Parameters
    ----------
    df                  : pd.DataFrame — raw floor data after column mapping
    col_map             : dict — mapping from required_name -> source_name
    stripping_standard  : str — \"IS456\" (default) or \"ACI347R-14\"
        IS456      -> IS 456:2000 Cl.11.3 SKU-based strip weeks (Indian standard)
        ACI347R-14 -> ACI 347R-14 S.5 flat 2-week buffer (American standard)
        If strip_week already exists in df, it is ALWAYS preserved unchanged.

    Academic basis
    --------------
    IS 456:2000 Cl.11.3 (BIS): mandatory Indian standard for stripping time.
    ACI 347R-14 S.5 (2014): American standard, retained as fallback.
    Hanna (1998) Ch.4: stripping time controls reuse eligibility window.
    """
    # If the user passed a dataframe that already has been renamed,
    # or passed col_map to do the renaming:
    valid_map = {v: k for k, v in col_map.items() if v and v != "--- Not in file ---"}
    # This might have happened in try2_real.py, but doing it again is safe.
    df = df.rename(columns=valid_map)

    required_cols = [
        "floor_id", "week_start", "week_end",
        "slab_area_m2", "wall_length_m", "col_count", "panel_type"
    ]

    # ── Auto-derive wall_length_m if absent (bridge/pier datasets) ───────
    # Peurifoy & Oberlender (2010): wall/pier formwork perimeter can be
    # approximated as sqrt(slab/formwork area) × π for circular piers, or
    # 2√(area) for rectangular sections. We use 2√(area) as a safe lower bound.
    if "wall_length_m" not in df.columns and "slab_area_m2" in df.columns:
        df["wall_length_m"] = (df["slab_area_m2"] ** 0.5 * 2.0).round(2)
        st.info(
            "ℹ️ **wall_length_m** not mapped — auto-derived from formwork area "
            "(wall_length = 2 × √area). For pier/bridge datasets this is a "
            "safe structural approximation (Peurifoy & Oberlender, 2010)."
        )

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        # strip_week is auto-generated below if absent — not a hard stop
        hard_missing = [m for m in missing if m != "strip_week"]
        if hard_missing:
            st.error(f"Missing required mapped columns: {hard_missing}. Please map them.")
            st.stop()

    # Auto-generate strip_week if absent — IS456 or ACI347R-14
    # IS 456:2000 Cl.11.3: user-supplied values always take priority.
    # Hanna (1998) Ch.4: stripping time is primary reuse constraint.
    if "strip_week" not in df.columns or df["strip_week"].isnull().all():
        if stripping_standard == "IS456":
            # IS 456:2000 Cl.11.3 — SKU-specific minimum stripping time
            df["strip_week"] = df["week_end"] + get_strip_weeks_is456(df)
        else:
            # ACI 347R-14 S.5 — flat 2-week buffer
            df["strip_week"] = df["week_end"] + get_strip_weeks_aci(df)

    # Re-check required_cols now that strip_week is guaranteed
    required_cols_check = [
        "floor_id", "week_start", "week_end", "strip_week",
        "slab_area_m2", "wall_length_m", "col_count", "panel_type"
    ]
    still_missing = [c for c in required_cols_check if c not in df.columns]
    if still_missing:
        st.error(f"Missing required columns after auto-generation: {still_missing}. Please map them.")
        st.stop()

    # Check A — No nulls in any of the 8 columns (including strip_week now guaranteed)
    null_mask = df[required_cols_check].isnull().any(axis=1)
    if null_mask.any():
        bad_rows = df[null_mask].index.tolist()
        st.error(f"Missing values found in rows: {bad_rows}. Fill these before uploading.")
        st.stop()

    # Check B — floor_id uniqueness
    # For bridge/pier datasets, Pier ID repeats per lift (one row per lift per pier).
    # We auto-create a composite key rather than stopping — warn the user.
    if df["floor_id"].duplicated().any():
        n_dupes = df["floor_id"].duplicated().sum()
        st.warning(
            f"⚠️ {n_dupes} duplicate floor_id values detected. "
            "This is normal for bridge/pier datasets (one row per lift). "
            "A unique composite ID (floor_id + row index) has been applied automatically."
        )
        # Create composite key: original id + underscore + lift/row index
        df = df.copy()
        df["floor_id"] = (
            df["floor_id"].astype(str)
            + "_L"
            + df.groupby("floor_id").cumcount().add(1).astype(str)
        )

    # Check C — schedule logic: strip_week >= week_end for every row
    bad_strip = df[df["strip_week"] < df["week_end"]]
    if not bad_strip.empty:
        st.error(f"strip_week is before week_end in rows: {bad_strip.index.tolist()}. Panels cannot be stripped before construction ends.")
        st.stop()

    # Check D — slab_area_m2 and wall_length_m are positive
    bad_area = df[(df["slab_area_m2"] <= 0) | (df["wall_length_m"] <= 0)]
    if not bad_area.empty:
        st.error(f"Non-positive area or wall length in rows: {bad_area.index.tolist()}.")
        st.stop()

    # Check E — col_count is a positive integer
    if not pd.api.types.is_integer_dtype(df["col_count"]):
        df["col_count"] = pd.to_numeric(df["col_count"], errors="coerce").astype("Int64")
    bad_col = df[df["col_count"] <= 0]
    if not bad_col.empty:
        st.error(f"col_count must be a positive integer. Bad rows: {bad_col.index.tolist()}.")
        st.stop()

    # Check F — panel_type is a known SKU
    KNOWN_SKUS = ["ALU-600", "ALU-450", "H20-beam"]
    unknown = df[~df["panel_type"].isin(KNOWN_SKUS)]["panel_type"].unique()
    if len(unknown) > 0:
        st.warning(f"Unrecognized panel types: {unknown.tolist()}. These will be processed but not matched to standard cost data. Add costs manually in sidebar.")

    # ── Optional formwork area columns ──────────────────────────────────
    # Based on: IS 1200 Part 1 (1992) — standard BoQ line items for
    # superstructure formwork in Indian construction.
    # Auto-generated if absent; user-supplied values override.

    auto_generated_cols = []

    if "col_shuttering_m2" not in df.columns:
        # Column shuttering area estimate:
        # col_count x average perimeter (2m) x floor height (3m)
        # IS 1200: column shuttering measured as contact area
        df["col_shuttering_m2"] = (
            df["col_count"] * 2.0 * 3.0
        ).round(2)
        auto_generated_cols.append(
            "col_shuttering_m2 (col_count x 2m perimeter x 3m height)"
        )

    if "beam_shuttering_m2" not in df.columns:
        # Beam shuttering area estimate:
        # wall_length x average beam soffit width (0.45m)
        # Covers slab beams + tie beams (Hanna 1998, Ch.4)
        df["beam_shuttering_m2"] = (
            df["wall_length_m"] * 0.45
        ).round(2)
        auto_generated_cols.append(
            "beam_shuttering_m2 (wall_length x 0.45m beam soffit)"
        )

    if "staircase_m2" not in df.columns:
        # Staircase shuttering: fixed estimate per floor
        # IS 1200: staircase measured separately from slab
        # Default 25 m2 covers typical residential stair flight
        df["staircase_m2"] = 25.0
        auto_generated_cols.append(
            "staircase_m2 (fixed 25 m2 per floor -- IS 1200 default)"
        )

    # Check G -- floor_override column (optional)
    # Leys et al. (2013). J.Exp.Social Psych. 49(4) 764-766:
    #   MAD cannot distinguish intentional from unintentional deviation.
    #   Human override is the correct resolution for known special causes.
    # Montgomery (2019). Statistical Quality Control 8th ed. Ch.6:
    #   Process control charts always allow operator override for special causes.
    # This is NEVER a hard stop. Files without floor_override continue unchanged.
    if "floor_override" in df.columns:
        df["floor_override"] = df["floor_override"].fillna(False).astype(bool)
    else:
        df["floor_override"] = False  # default: no floors overridden

    return df, auto_generated_cols
