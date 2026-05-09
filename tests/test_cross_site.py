"""tests/test_cross_site.py — pytest suite for backend/core/cross_site.py"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.cross_site import collect_idle_panels, match_supply_to_demand


SAMPLE_BOQ = [
    {"sku": "ALU-600", "week": 3, "idle": 50, "procure": 0},
    {"sku": "ALU-450", "week": 4, "idle": 30, "procure": 0},
    {"sku": "ALU-600", "week": 5, "idle": 0,  "procure": 10},
]


def test_collect_idle_filters_zero():
    result = collect_idle_panels("Site A", SAMPLE_BOQ)
    assert len(result) == 2
    assert all(r["idle_qty"] > 0 for r in result)


def test_collect_idle_sets_site():
    result = collect_idle_panels("Site X", SAMPLE_BOQ)
    assert all(r["site"] == "Site X" for r in result)


def test_match_finds_cross_site():
    idle = [{"site": "Site A", "sku": "ALU-600", "week": 3, "idle_qty": 50}]
    demand = [{"site": "Site B", "sku": "ALU-600", "week": 5, "procure_qty": 40}]
    matches = match_supply_to_demand(idle, demand)
    assert len(matches) == 1
    assert matches[0]["from_site"] == "Site A"
    assert matches[0]["to_site"]   == "Site B"
    assert matches[0]["qty"]       == 40


def test_match_same_site_not_matched():
    idle   = [{"site": "Site A", "sku": "ALU-600", "week": 3, "idle_qty": 50}]
    demand = [{"site": "Site A", "sku": "ALU-600", "week": 5, "procure_qty": 30}]
    matches = match_supply_to_demand(idle, demand)
    assert len(matches) == 0


def test_match_timing_constraint():
    # idle available in week 5, needed in week 5 — fails (need available before)
    idle   = [{"site": "Site A", "sku": "ALU-600", "week": 5, "idle_qty": 50}]
    demand = [{"site": "Site B", "sku": "ALU-600", "week": 5, "procure_qty": 30}]
    matches = match_supply_to_demand(idle, demand)
    assert len(matches) == 0


def test_match_does_not_double_allocate():
    idle   = [{"site": "Site A", "sku": "ALU-600", "week": 1, "idle_qty": 20}]
    demand = [
        {"site": "Site B", "sku": "ALU-600", "week": 3, "procure_qty": 20},
        {"site": "Site C", "sku": "ALU-600", "week": 4, "procure_qty": 20},
    ]
    matches = match_supply_to_demand(idle, demand)
    assert len(matches) == 1  # only first demand satisfied
