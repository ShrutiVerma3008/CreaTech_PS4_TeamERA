# FormOptiX backend/core — algorithmic engines
from .clustering import compute_repetition_score
from .lp_optimizer import run_sku_optimizer, compute_baseline
from .freeze_guard import (
    compute_design_freeze,
    identify_unstable_floors,
    estimate_rework_cost,
    get_procurement_recommendation,
)
from .cross_site import collect_idle_panels, match_supply_to_demand

__all__ = [
    "compute_repetition_score",
    "run_sku_optimizer",
    "compute_baseline",
    "compute_design_freeze",
    "identify_unstable_floors",
    "estimate_rework_cost",
    "get_procurement_recommendation",
    "collect_idle_panels",
    "match_supply_to_demand",
]
