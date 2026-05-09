"""tests/test_synthetic_data.py — pytest suite for backend/utils/synthetic_data.py"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.synthetic_data import generate_building_data, simulate_forecast


def test_generate_correct_row_count():
    df_floors, df_schedule = generate_building_data(n_floors=15, seed=0)
    assert len(df_floors) == 15
    assert len(df_schedule) == 52


def test_generate_has_required_columns():
    df_floors, _ = generate_building_data(n_floors=10, seed=1)
    for col in ("floor_id", "floor_name", "floor_type", "slab_area_sqm",
                "wall_length_m", "column_count", "beam_count"):
        assert col in df_floors.columns


def test_generate_floor_types_include_typical():
    df_floors, _ = generate_building_data(n_floors=20, seed=42)
    assert "Typical" in df_floors["floor_type"].values


def test_generate_deterministic():
    df1, _ = generate_building_data(20, seed=99)
    df2, _ = generate_building_data(20, seed=99)
    assert df1["slab_area_sqm"].sum() == df2["slab_area_sqm"].sum()


def test_schedule_demand_columns():
    _, df_schedule = generate_building_data(20, seed=0)
    for col in ("wall_panels_demand", "slab_panels_demand", "col_panels_demand"):
        assert col in df_schedule.columns
        assert (df_schedule[col] >= 0).all()


def test_simulate_forecast_lengths():
    _, df_schedule = generate_building_data(20, seed=0)
    weeks, demand, forecast, upper, lower = simulate_forecast(df_schedule)
    assert len(weeks) == len(demand) == len(forecast) == len(upper) == len(lower)


def test_simulate_forecast_bounds():
    _, df_schedule = generate_building_data(20, seed=0)
    _, _, forecast, upper, lower = simulate_forecast(df_schedule)
    assert (upper >= forecast).all()
    assert (lower >= 0).all()
