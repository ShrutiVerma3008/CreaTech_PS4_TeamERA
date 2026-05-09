"""
backend/utils/data_loader.py
FormOptiX — Excel Input Validation & Column Mapping

Raises ValueError on bad data so the caller (frontend or tests) can handle it
appropriately. No Streamlit dependency — pure Python.
"""

import pandas as pd


# Known panel SKUs recognised by the cost model
KNOWN_SKUS = ["ALU-600", "ALU-450", "H20-beam"]


def validate_and_map(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    """
    Rename user columns to canonical names and validate data integrity.

    Parameters
    ----------
    df      : Raw DataFrame from the uploaded Excel file.
    col_map : {canonical_name: user_column_name} mapping chosen in the UI.
              Values equal to "--- Not in file ---" are skipped.

    Returns
    -------
    Validated, renamed DataFrame ready for backend processing.

    Raises
    ------
    ValueError
        With a human-readable message describing the first validation failure.
        The frontend should catch this and display it via st.error().
    """
    # Apply column renaming
    valid_map = {v: k for k, v in col_map.items() if v and v != "--- Not in file ---"}
    df = df.rename(columns=valid_map)

    required_cols = [
        "floor_id", "week_start", "week_end", "strip_week",
        "slab_area_m2", "wall_length_m", "col_count", "panel_type",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required mapped columns: {missing}. "
            "Please map them in the column-mapping section."
        )

    # Check A — No nulls in any of the 8 required columns
    null_mask = df[required_cols].isnull().any(axis=1)
    if null_mask.any():
        bad_rows = df[null_mask].index.tolist()
        raise ValueError(
            f"Missing values found in rows: {bad_rows}. "
            "Fill these before uploading."
        )

    # Check B — floor_id has no duplicates
    if df["floor_id"].duplicated().any():
        dupes = df[df["floor_id"].duplicated()]["floor_id"].tolist()
        raise ValueError(
            f"Duplicate floor IDs found: {dupes}. Each floor must appear once."
        )

    # Check C — schedule logic: strip_week >= week_end for every row
    bad_strip = df[df["strip_week"] < df["week_end"]]
    if not bad_strip.empty:
        raise ValueError(
            f"strip_week is before week_end in rows: {bad_strip.index.tolist()}. "
            "Panels cannot be stripped before construction ends."
        )

    # Check D — slab_area_m2 and wall_length_m are positive
    bad_area = df[(df["slab_area_m2"] <= 0) | (df["wall_length_m"] <= 0)]
    if not bad_area.empty:
        raise ValueError(
            f"Non-positive area or wall length in rows: {bad_area.index.tolist()}."
        )

    # Check E — col_count is a positive integer
    if not pd.api.types.is_integer_dtype(df["col_count"]):
        df["col_count"] = pd.to_numeric(df["col_count"], errors="coerce").astype("Int64")
    bad_col = df[df["col_count"] <= 0]
    if not bad_col.empty:
        raise ValueError(
            f"col_count must be a positive integer. Bad rows: {bad_col.index.tolist()}."
        )

    # Check F — panel_type is a known SKU (warning, not error)
    unknown = df[~df["panel_type"].isin(KNOWN_SKUS)]["panel_type"].unique()
    if len(unknown) > 0:
        import warnings
        warnings.warn(
            f"Unrecognized panel types: {unknown.tolist()}. "
            "These will be processed but not matched to standard cost data. "
            "Add costs manually in sidebar.",
            stacklevel=2,
        )

    return df
