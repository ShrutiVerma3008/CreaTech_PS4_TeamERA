"""tests/test_data_loader.py — pytest suite for backend/utils/data_loader.py"""

import pytest
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.data_loader import validate_and_map


def _good_df():
    return pd.DataFrame({
        "floor_id":     ["F01", "F02", "F03"],
        "week_start":   [1, 3, 7],
        "week_end":     [3, 5, 9],
        "strip_week":   [5, 7, 11],
        "slab_area_m2": [850.0, 860.0, 855.0],
        "wall_length_m":[420.0, 418.0, 422.0],
        "col_count":    [24, 24, 24],
        "panel_type":   ["ALU-600", "ALU-600", "ALU-450"],
    })


def _identity_map():
    cols = ["floor_id", "week_start", "week_end", "strip_week",
            "slab_area_m2", "wall_length_m", "col_count", "panel_type"]
    return {c: c for c in cols}


def test_valid_data_passes():
    df = validate_and_map(_good_df(), _identity_map())
    assert len(df) == 3


def test_missing_required_column_raises():
    df = _good_df().drop(columns=["strip_week"])
    with pytest.raises(ValueError, match="Missing required mapped columns"):
        validate_and_map(df, _identity_map())


def test_duplicate_floor_id_raises():
    df = _good_df()
    df.loc[2, "floor_id"] = "F01"
    with pytest.raises(ValueError, match="Duplicate floor IDs"):
        validate_and_map(df, _identity_map())


def test_strip_before_end_raises():
    df = _good_df()
    df.loc[0, "strip_week"] = 2   # strip_week < week_end
    with pytest.raises(ValueError, match="strip_week is before week_end"):
        validate_and_map(df, _identity_map())


def test_non_positive_area_raises():
    df = _good_df()
    df.loc[0, "slab_area_m2"] = 0.0
    with pytest.raises(ValueError, match="Non-positive area"):
        validate_and_map(df, _identity_map())


def test_col_map_rename():
    df = _good_df().rename(columns={"floor_id": "ID"})
    col_map = _identity_map()
    col_map["floor_id"] = "ID"
    result = validate_and_map(df, col_map)
    assert "floor_id" in result.columns
