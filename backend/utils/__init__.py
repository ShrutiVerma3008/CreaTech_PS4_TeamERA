# FormOptiX backend/utils — data loading, computation, reporting
from .data_loader import validate_and_map
from .demand_calc import build_reuse_matrix
from .synthetic_data import generate_building_data, simulate_forecast

# report_generator requires reportlab — imported lazily to avoid
# breaking environments where reportlab is not installed.
def generate_boq_pdf(*args, **kwargs):
    from .report_generator import generate_boq_pdf as _gen
    return _gen(*args, **kwargs)

__all__ = [
    "validate_and_map",
    "build_reuse_matrix",
    "generate_building_data",
    "simulate_forecast",
    "generate_boq_pdf",
]
