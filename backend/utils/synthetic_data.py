"""
backend/utils/synthetic_data.py
FormOptiX — Synthetic Building Data Generator & Demand Forecaster

Extracted from the monolithic app file. Pure Python — no Streamlit dependency.
"""

import numpy as np
import pandas as pd


def generate_building_data(n_floors: int = 20, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate a synthetic floor dataset and a 52-week demand schedule.

    Parameters
    ----------
    n_floors : int  — number of floors in the building (10–40)
    seed     : int  — numpy random seed for reproducibility

    Returns
    -------
    df_floors   : DataFrame — one row per floor with geometry features
    df_schedule : DataFrame — one row per week with panel demand counts
    """
    np.random.seed(seed)
    floor_types = []
    for i in range(n_floors):
        if i == 0:
            ft = "Basement"
        elif i <= 2:
            ft = "Podium"
        elif i == n_floors - 1:
            ft = "Terrace"
        elif i % 7 == 0:
            ft = "Refuge"
        else:
            ft = "Typical"
        floor_types.append(ft)

    base_slab = 850
    base_wall = 420
    base_col  = 24
    base_beam = 18

    floors = []
    for i in range(n_floors):
        ft = floor_types[i]
        if ft == "Typical":
            var  = 0.05
            slab = base_slab * np.random.uniform(1 - var, 1 + var)
            wall = base_wall * np.random.uniform(1 - var, 1 + var)
            col  = int(base_col * np.random.uniform(0.95, 1.05))
            beam = int(base_beam * np.random.uniform(0.95, 1.05))
        elif ft == "Podium":
            slab = base_slab * np.random.uniform(1.3, 1.5)
            wall = base_wall * np.random.uniform(1.2, 1.4)
            col  = int(base_col * 1.3)
            beam = int(base_beam * 1.2)
        elif ft == "Refuge":
            slab = base_slab * np.random.uniform(0.9, 1.0)
            wall = base_wall * np.random.uniform(1.1, 1.2)
            col  = base_col
            beam = base_beam
        elif ft == "Terrace":
            slab = base_slab * np.random.uniform(0.7, 0.85)
            wall = base_wall * np.random.uniform(0.6, 0.75)
            col  = int(base_col * 0.8)
            beam = int(base_beam * 0.75)
        else:  # Basement
            slab = base_slab * 1.6
            wall = base_wall * 1.5
            col  = int(base_col * 1.5)
            beam = int(base_beam * 1.4)

        floors.append({
            "floor_id":       i,
            "floor_name":     f"F{i:02d}",
            "floor_type":     ft,
            "slab_area_sqm":  round(slab, 1),
            "wall_length_m":  round(wall, 1),
            "column_count":   col,
            "beam_count":     beam,
        })

    df = pd.DataFrame(floors)

    # 52-week demand schedule
    weeks = []
    floors_per_week = max(1, n_floors // 18)
    for w in range(1, 53):
        active_start = min(int((w - 1) * n_floors / 52), n_floors - 1)
        active_end   = min(active_start + floors_per_week, n_floors)
        active_floors = list(range(active_start, active_end))
        if not active_floors:
            active_floors = [active_start]
        total_slab   = df.loc[df.floor_id.isin(active_floors), "slab_area_sqm"].sum()
        wall_panels  = int(total_slab / 8.5  * np.random.uniform(0.95, 1.05))
        slab_panels  = int(total_slab / 12.0 * np.random.uniform(0.95, 1.05))
        col_panels   = int(total_slab / 18.0 * np.random.uniform(0.95, 1.05))
        weeks.append({
            "week":                w,
            "active_floors":       active_floors,
            "wall_panels_demand":  max(10, wall_panels),
            "slab_panels_demand":  max(8,  slab_panels),
            "col_panels_demand":   max(5,  col_panels),
        })

    return df, pd.DataFrame(weeks)


def simulate_forecast(df_schedule: pd.DataFrame) -> tuple:
    """
    Generate a simulated demand forecast with confidence intervals.

    Parameters
    ----------
    df_schedule : schedule DataFrame with 'week' and 'wall_panels_demand' columns

    Returns
    -------
    (weeks, demand, forecast, upper, lower) — all numpy arrays
    """
    weeks    = df_schedule["week"].values
    demand   = df_schedule["wall_panels_demand"].values

    trend    = np.linspace(demand[0], demand[-1], len(weeks))
    seasonal = 8 * np.sin(2 * np.pi * weeks / 12)
    noise    = np.random.normal(0, 3, len(weeks))
    forecast = np.clip(trend + seasonal + noise, 5, None).astype(int)
    upper    = forecast + np.random.randint(5, 18, len(weeks))
    lower    = np.maximum(0, forecast - np.random.randint(3, 12, len(weeks)))

    return weeks, demand, forecast, upper, lower
