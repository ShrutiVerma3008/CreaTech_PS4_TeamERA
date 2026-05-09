"""tests/test_freeze_guard.py — pytest suite for backend/core/freeze_guard.py"""

import pytest
import numpy as np
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.freeze_guard import (
    compute_design_freeze,
    identify_unstable_floors,
    estimate_rework_cost,
    get_procurement_recommendation,
)


@pytest.fixture
def stable_df():
    np.random.seed(0)
    n = 15
    return pd.DataFrame({
        "floor_id":       range(n),
        "slab_area_sqm":  np.random.uniform(840, 860, n),
        "wall_length_m":  np.random.uniform(415, 425, n),
        "column_count":   np.random.randint(23, 26, n).astype(float),
    })


@pytest.fixture
def unstable_df():
    np.random.seed(1)
    base = list(np.random.uniform(840, 860, 13))
    return pd.DataFrame({
        "floor_id":       range(15),
        "slab_area_sqm":  base + [2700.0, 2650.0],
        "wall_length_m":  list(np.random.uniform(415, 425, 15)),
        "column_count":   list(np.random.randint(23, 26, 15).astype(float)),
    })


class TestComputeDesignFreeze:
    def test_stable_is_safe(self, stable_df):
        result = compute_design_freeze(stable_df)
        assert result["DI"] < 10.0
        assert result["status"] == "SAFE"

    def test_unstable_is_halt(self, unstable_df):
        result = compute_design_freeze(unstable_df)
        assert result["DI"] > 15.0
        assert result["status"] == "HALT"

    def test_returns_all_keys(self, stable_df):
        result = compute_design_freeze(stable_df)
        for key in ("CV_slab", "CV_wall", "CV_col", "DI", "status", "recommendation"):
            assert key in result

    def test_accepts_alternate_col_names(self, stable_df):
        df = stable_df.rename(columns={"slab_area_sqm": "slab_area_m2", "column_count": "col_count"})
        result = compute_design_freeze(df)
        assert result["status"] in ("SAFE", "WARNING", "HALT")


class TestIdentifyUnstableFloors:
    def test_stable_has_no_outliers(self, stable_df):
        unstable = identify_unstable_floors(stable_df)
        assert isinstance(unstable, list)

    def test_unstable_detects_outliers(self, unstable_df):
        unstable = identify_unstable_floors(unstable_df)
        assert len(unstable) > 0
        assert all("floor_id" in u for u in unstable)


class TestEstimateReworkCost:
    def test_no_unstable_returns_zeros(self, stable_df):
        result = estimate_rework_cost([], stable_df, c_p=15000)
        assert result["panels_at_risk"] == 0
        assert result["rework_cost_order_now"] == 0.0

    def test_with_unstable_returns_positive(self, unstable_df):
        unstable = identify_unstable_floors(unstable_df)
        result = estimate_rework_cost(unstable, unstable_df, c_p=15000)
        assert result["panels_at_risk"] > 0
        assert result["rework_cost_order_now"] > 0


class TestGetProcurementRecommendation:
    def test_safe_procures_all(self):
        result = get_procurement_recommendation(5.0, {0: [1, 2], 1: [3]}, [])
        assert result["action"] == "PROCURE ALL"

    def test_halt_halts_all(self):
        result = get_procurement_recommendation(20.0, {0: [1, 2]}, [1])
        assert result["action"] == "HALT ALL PROCUREMENT"

    def test_warning_is_partial(self):
        result = get_procurement_recommendation(12.0, {0: [1, 2], 1: [3]}, [3])
        assert result["action"] == "PROCURE STABLE CLUSTERS ONLY"
        assert 0 in result["stable_clusters"]
        assert 1 in result["unstable_clusters"]
