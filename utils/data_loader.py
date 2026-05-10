import pandas as pd
import streamlit as st

def validate_and_map(df, col_map):
    # If the user passed a dataframe that already has been renamed,
    # or passed col_map to do the renaming:
    valid_map = {v: k for k, v in col_map.items() if v and v != "--- Not in file ---"}
    # This might have happened in try2_real.py, but doing it again is safe.
    df = df.rename(columns=valid_map)

    required_cols = [
        "floor_id", "week_start", "week_end", "strip_week",
        "slab_area_m2", "wall_length_m", "col_count", "panel_type"
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing required mapped columns: {missing}. Please map them.")
        st.stop()

    # Check A — No nulls in any of the 8 columns
    null_mask = df[required_cols].isnull().any(axis=1)
    if null_mask.any():
        bad_rows = df[null_mask].index.tolist()
        st.error(f"Missing values found in rows: {bad_rows}. Fill these before uploading.")
        st.stop()

    # Check B — floor_id has no duplicates
    if df["floor_id"].duplicated().any():
        dupes = df[df["floor_id"].duplicated()]["floor_id"].tolist()
        st.error(f"Duplicate floor IDs found: {dupes}. Each floor must appear once.")
        st.stop()

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

    return df, auto_generated_cols
