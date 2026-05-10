"""
core/clustering.py
FormOptiX — DBSCAN Repetition Clustering with Physical Reuse Filter

Academic basis:
  Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). KDD-96, AAAI Press.
    → DBSCAN: density-based clustering without pre-specifying k.
  Hanna, A.S. (1998). Concrete Formwork Systems. Marcel Dekker. Chapter 4.
    → Panel cycling logistics; basis for physical reuse eligibility filter.
  Peurifoy, R.L., & Oberlender, G.D. (2010). Formwork for Concrete Structures
    (4th ed.). McGraw-Hill. Chapter 7.
    → Industry benchmark: 60-80% reuse rate on typical floors.
  ACI Committee 347. (2014). ACI 347R-14: Guide to Formwork for Concrete.
    American Concrete Institute. Section 5.
    → Minimum cure time before stripping; physical basis for strip_week constraint.
"""

import numpy as np
import pandas as pd

try:
    import streamlit as st
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False

try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from utils.demand_calc import build_reuse_matrix


def _warn(msg: str) -> None:
    """Emit a warning via Streamlit if available, otherwise print."""
    if _ST_AVAILABLE:
        st.warning(msg)
    else:
        print(f"WARNING: {msg}")


def generate_kit_families(df: pd.DataFrame, cluster_labels: np.ndarray) -> list:
    """
    cluster_labels: array of int labels from DBSCAN (-1 = noise)
    Returns: list of dicts, one per non-noise cluster, sorted by cluster id.

    Each dict:
    {
      "kit_id":           "Kit A", "Kit B", ... (alphabetic)
      "cluster_id":       int
      "floor_ids":        list of floor_id strings
      "floor_count":      int
      "avg_slab_area":    float (mean slab_area_m2, rounded 1dp)
      "avg_wall_length":  float (mean wall_length_m, rounded 1dp)
      "avg_col_count":    float (mean col_count, rounded 1dp)
      "est_wall_panels":  int   (from formula above, using mean values)
      "est_slab_panels":  int
      "est_corner_pieces":int
      "est_transport_trips": int
      "reuse_potential":  "HIGH" if floor_count >= 6
                          "MEDIUM" if floor_count >= 3
                          "LOW" otherwise
      "primary_sku":      most common panel_type in this cluster's floors
    }
    Noise floors (label == -1) are collected into one entry with
    kit_id = "Custom Kit" and reuse_potential = "LOW".
    """
    if df.empty or len(df) != len(cluster_labels):
        return []

    area_col = "slab_area_sqm" if "slab_area_sqm" in df.columns else "slab_area_m2"
    wall_col = "wall_length_m"
    col_col  = "column_count" if "column_count" in df.columns else "col_count"
    id_col   = "floor_id"

    kit_families = []

    # Process non-noise clusters
    unique_clusters = sorted([k for k in set(cluster_labels) if k != -1])

    for idx, k in enumerate(unique_clusters):
        mask = cluster_labels == k
        subset = df[mask]

        avg_slab = float(subset[area_col].mean()) if not subset[area_col].isna().all() else 0.0
        avg_wall = float(subset[wall_col].mean()) if not subset[wall_col].isna().all() else 0.0
        avg_col  = float(subset[col_col].mean()) if not subset[col_col].isna().all() else 0.0

        wall_panels = int(np.ceil(avg_wall / 0.6))
        slab_panels = int(np.ceil(avg_slab / 0.36))
        corner_pieces = int(np.round(avg_col * 2))
        transport_trips = int(np.ceil((wall_panels + slab_panels) / 40.0))

        floor_count = len(subset)
        if floor_count >= 6:
            reuse_pot = "HIGH"
        elif floor_count >= 3:
            reuse_pot = "MEDIUM"
        else:
            reuse_pot = "LOW"

        prim_sku = subset["panel_type"].mode()[0] if "panel_type" in subset.columns and not subset["panel_type"].mode().empty else "Unknown"

        kit_families.append({
            "kit_id": f"Kit {chr(65 + idx)}",
            "cluster_id": k,
            "floor_ids": subset[id_col].astype(str).tolist(),
            "floor_count": floor_count,
            "avg_slab_area": round(avg_slab, 1),
            "avg_wall_length": round(avg_wall, 1),
            "avg_col_count": round(avg_col, 1),
            "est_wall_panels": wall_panels,
            "est_slab_panels": slab_panels,
            "est_corner_pieces": corner_pieces,
            "est_transport_trips": transport_trips,
            "reuse_potential": reuse_pot,
            "primary_sku": prim_sku,
        })

    # Process noise cluster
    noise_mask = cluster_labels == -1
    if noise_mask.any():
        subset = df[noise_mask]
        avg_slab = float(subset[area_col].mean()) if not subset[area_col].isna().all() else 0.0
        avg_wall = float(subset[wall_col].mean()) if not subset[wall_col].isna().all() else 0.0
        avg_col  = float(subset[col_col].mean()) if not subset[col_col].isna().all() else 0.0

        wall_panels = int(np.ceil(avg_wall / 0.6))
        slab_panels = int(np.ceil(avg_slab / 0.36))
        corner_pieces = int(np.round(avg_col * 2))
        transport_trips = int(np.ceil((wall_panels + slab_panels) / 40.0))

        prim_sku = subset["panel_type"].mode()[0] if "panel_type" in subset.columns and not subset["panel_type"].mode().empty else "Unknown"

        kit_families.append({
            "kit_id": "Custom Kit",
            "cluster_id": -1,
            "floor_ids": subset[id_col].astype(str).tolist(),
            "floor_count": len(subset),
            "avg_slab_area": round(avg_slab, 1),
            "avg_wall_length": round(avg_wall, 1),
            "avg_col_count": round(avg_col, 1),
            "est_wall_panels": wall_panels,
            "est_slab_panels": slab_panels,
            "est_corner_pieces": corner_pieces,
            "est_transport_trips": transport_trips,
            "reuse_potential": "LOW",
            "primary_sku": prim_sku,
        })

    return kit_families


# ──────────────────────────────────────────────────────────────────────────────
# KIT SPECIFICATION — Panel Counts per Kit
# ──────────────────────────────────────────────────────────────────────────────

# Default SKU coverage ratios (m² of formwork area covered per panel unit).
# Based on Peurifoy & Oberlender (2010), Ch.7 — standard European panel sizes:
#   ALU-600  : 0.6 m × 1.2 m = 0.72 m² effective coverage per wall/slab unit
#   ALU-450  : 0.45 m × 0.9 m = 0.405 m² effective coverage (column/corner)
#   H20-beam : used for slab bearing; 1 beam covers ~1.5 m² of slab soffit
DEFAULT_SKU_COVERAGE = {
    "ALU-600":  0.72,   # m² per wall/slab panel   — Peurifoy & Oberlender (2010) Ch.7
    "ALU-450":  0.405,  # m² per column panel       — Peurifoy & Oberlender (2010) Ch.7
    "H20-beam": 1.50,   # m² per slab soffit beam   — Peurifoy & Oberlender (2010) Ch.7
}


def generate_kit_specification(
    kit_families: list,
    df: pd.DataFrame,
    sku_coverage_ratios: dict | None = None,
) -> pd.DataFrame:
    """
    Derive a panel-count specification per Formwork Kit Family and SKU.

    Academic basis
    --------------
    Peurifoy, R.L., & Oberlender, G.D. (2010). Formwork for Concrete
    Structures (4th ed.). McGraw-Hill. Chapter 7.
        → Coverage ratios: panel area ÷ floor area gives panel count.
        → 10% buffer is a standard site contingency for damage/miscounting.

    Parameters
    ----------
    kit_families       : list of dicts returned by generate_kit_families().
    df                 : the validated floor DataFrame (must contain the area
                         column — slab_area_sqm or slab_area_m2).
    sku_coverage_ratios: dict of {sku_label: m2_per_panel}.  Defaults to
                         DEFAULT_SKU_COVERAGE if None or empty.

    Returns
    -------
    pd.DataFrame with columns:
        kit_id          : str   — e.g. "Kit A", "Custom Kit"
        sku             : str   — e.g. "ALU-600"
        avg_area_m2     : float — mean slab area of floors in this kit
        panel_count     : int   — ceil(avg_area_m2 / coverage_ratio)
        buffer_panels   : int   — ceil(panel_count × 0.10)
        total_panels    : int   — panel_count + buffer_panels

    Returns an empty DataFrame (with the correct columns) when kit_families
    is empty or no valid area column is found.
    """
    _COLS = ["kit_id", "sku", "avg_area_m2", "panel_count", "buffer_panels", "total_panels"]

    if not kit_families:
        return pd.DataFrame(columns=_COLS)

    ratios = dict(DEFAULT_SKU_COVERAGE)
    if sku_coverage_ratios:
        ratios.update(sku_coverage_ratios)

    area_col = "slab_area_sqm" if "slab_area_sqm" in df.columns else "slab_area_m2"
    if area_col not in df.columns:
        return pd.DataFrame(columns=_COLS)

    rows: list[dict] = []

    for kit in kit_families:
        kit_id    = kit["kit_id"]
        floor_ids = kit["floor_ids"]

        # Mean area for the floors belonging to this kit
        # Use the already-computed avg_slab_area if available (avoids
        # re-filtering df for every SKU — single pass per kit).
        avg_area = kit.get("avg_slab_area")
        if avg_area is None or avg_area == 0:
            subset   = df[df["floor_id"].astype(str).isin([str(f) for f in floor_ids])]
            avg_area = float(subset[area_col].mean()) if len(subset) > 0 else 0.0

        avg_area = round(float(avg_area), 2)

        for sku, cov in ratios.items():
            if cov <= 0:
                continue
            panel_count   = int(np.ceil(avg_area / cov))
            buffer_panels = int(np.ceil(panel_count * 0.10))
            total_panels  = panel_count + buffer_panels

            rows.append({
                "kit_id":        kit_id,
                "sku":           sku,
                "avg_area_m2":   avg_area,
                "panel_count":   panel_count,
                "buffer_panels": buffer_panels,
                "total_panels":  total_panels,
            })

    if not rows:
        return pd.DataFrame(columns=_COLS)

    return pd.DataFrame(rows, columns=_COLS)


# ──────────────────────────────────────────────────────────────────────────────
# MULTI-TYPE KIT SPECIFICATION — IS 1200 BoQ Line Items (Gap 1 v2)
# ──────────────────────────────────────────────────────────────────────────────

def compute_kit_specification(cluster_df: "pd.DataFrame", coverage_ratios: dict) -> list:
    """
    Compute formwork kit specification for a cluster of floors.

    Returns a list of 4 dicts, one per IS 1200 formwork type:
        {
            "Formwork Type"  : str,
            "IS 1200 Ref"    : str,
            "Total Area (m2)": float,
            "Panels Required": int,   # ceil(area/coverage) * 1.10 buffer
            "SKU"            : str,
        }

    Academic basis
    --------------
    IS 1200 Part 1 (1992) -- formwork measurement standard for Indian BoQ.
        Item 16  : Column shuttering (super-structure)
        Item 20a : Slab beam shuttering
        Item 20b : Slab bottom shuttering
        Item 29  : Staircase shuttering
    Hanna, A.S. (1998). Concrete Formwork Systems. Marcel Dekker, Ch.4.
        -- Panel coverage ratios and assembly logic.
    Peurifoy, R.L., & Oberlender, G.D. (2010). Formwork for Concrete
        Structures (4th ed.). McGraw-Hill, Ch.7.
        -- 10% contingency buffer; kit assembly from floor geometry.
    """
    import math

    area_col = "slab_area_m2" if "slab_area_m2" in cluster_df.columns else "slab_area_sqm"

    # Sum areas across all floors in this cluster
    total_slab_area  = float(cluster_df[area_col].sum()) if area_col in cluster_df.columns else 0.0
    total_col_area   = float(cluster_df["col_shuttering_m2"].sum()) if "col_shuttering_m2" in cluster_df.columns else 0.0
    total_beam_area  = float(cluster_df["beam_shuttering_m2"].sum()) if "beam_shuttering_m2" in cluster_df.columns else 0.0
    total_stair_area = float(cluster_df["staircase_m2"].sum()) if "staircase_m2" in cluster_df.columns else 0.0

    BUFFER = 1.10  # 10% buffer -- standard site practice (Peurifoy & Oberlender 2010 Ch.7)

    def _panels(area: float, coverage: float) -> int:
        if coverage <= 0 or area <= 0:
            return 0
        return math.ceil(area / coverage * BUFFER)

    kit = [
        {
            "Formwork Type":    "Slab Bottom Shuttering",
            "IS 1200 Ref":      "Item 20b",
            "Total Area (m2)":  round(total_slab_area, 1),
            "Panels Required":  _panels(total_slab_area, coverage_ratios.get("slab", 1.2)),
            "SKU":              "ALU-600",
        },
        {
            "Formwork Type":    "Slab Beam Shuttering",
            "IS 1200 Ref":      "Item 20a",
            "Total Area (m2)":  round(total_beam_area, 1),
            "Panels Required":  _panels(total_beam_area, coverage_ratios.get("beam", 0.6)),
            "SKU":              "H20-beam",
        },
        {
            "Formwork Type":    "Column Shuttering (Super)",
            "IS 1200 Ref":      "Item 16",
            "Total Area (m2)":  round(total_col_area, 1),
            "Panels Required":  _panels(total_col_area, coverage_ratios.get("col", 0.9)),
            "SKU":              "ALU-450",
        },
        {
            "Formwork Type":    "Staircase Shuttering",
            "IS 1200 Ref":      "Item 29",
            "Total Area (m2)":  round(total_stair_area, 1),
            "Panels Required":  _panels(total_stair_area, coverage_ratios.get("stair", 0.5)),
            "SKU":              "Custom",
        },
    ]
    return kit


def compute_repetition_score(
    df_floors: pd.DataFrame,
    transport_weeks: int = 1,
) -> tuple:
    """
    Run DBSCAN on floor geometry, then apply the physical reuse filter.

    Parameters
    ----------
    df_floors : pd.DataFrame
        Floor dataframe.  Must contain:
          slab_area_sqm / slab_area_m2, wall_length_m, column_count / col_count,
          beam_count (optional), floor_id, week_start, week_end, strip_week.
        Synthetic-mode data uses slab_area_sqm / column_count / beam_count.
        Real-mode data uses slab_area_m2 / col_count (mapped by validate_and_map).
    transport_weeks : int, default 1
        Sidebar input — time (weeks) to move panels between floors.

    Returns
    -------
    df_floors       : DataFrame with 'cluster' and 'rho_k' columns added.
    repetition_score: float — percentage of floors in the dominant cluster.
    cluster_summary : DataFrame — per-cluster stats.
    rho_k_map       : dict  — {cluster_label: rho_k value}.
    reuse_pairs     : list  — list of dicts for the valid-reuse-pairs table.
    overall_reuse   : float — portfolio-wide reuse rate (0–1).
    kit_families    : list  — list of dicts describing the kit families.
    """
    # ── Normalise column names for both synthetic and real modes ──────────
    df = df_floors.copy()

    area_col   = "slab_area_sqm" if "slab_area_sqm" in df.columns else "slab_area_m2"
    wall_col   = "wall_length_m"
    col_col    = "column_count" if "column_count" in df.columns else "col_count"
    beam_col   = "beam_count" if "beam_count" in df.columns else None
    id_col     = "floor_id"

    feature_cols = [area_col, wall_col, col_col]
    if beam_col and beam_col in df.columns:
        feature_cols.append(beam_col)

    features = df[feature_cols].values.astype(float)

    # ── DBSCAN clustering (Ester et al., 1996) ────────────────────────────
    if SKLEARN_AVAILABLE:
        scaler = StandardScaler()
        X = scaler.fit_transform(features)
        db = DBSCAN(eps=0.8, min_samples=2).fit(X)
        labels = db.labels_
    else:
        # Fallback: manual distance-based grouping
        norms = (features - features.mean(0)) / (features.std(0) + 1e-9)
        labels = np.zeros(len(features), dtype=int)
        for i in range(len(norms)):
            dists = np.linalg.norm(norms - norms[i], axis=1)
            if dists[dists < 1.0].sum() > 2:
                labels[i] = 1
            else:
                labels[i] = -1 if dists.min() > 1.5 else 0

    df["cluster"] = labels

    # ── Physical reuse filter — Hanna (1998) Ch.4 ────────────────────────
    # Geometric similarity alone (DBSCAN) is not sufficient.
    # Panels must also be available in time (strip + transport).
    # Clusters with zero valid reuse pairs are reclassified as noise.
    has_schedule = all(c in df.columns for c in ["week_start", "week_end", "strip_week"])

    rho_k_map     = {}
    reuse_pairs   = []
    total_vp_all  = 0
    total_tp_all  = 0

    if has_schedule:
        eligible_matrix = build_reuse_matrix(df[[id_col, "week_start", "week_end", "strip_week"]], transport_weeks)

        unique_clusters = [k for k in df["cluster"].unique() if k != -1]

        for k in unique_clusters:
            cluster_mask  = df["cluster"] == k
            cluster_ids   = df.loc[cluster_mask, id_col].tolist()
            n             = len(cluster_ids)

            # Extract sub-matrix for this cluster
            sub = eligible_matrix.loc[
                [i for i in cluster_ids if i in eligible_matrix.index],
                [i for i in cluster_ids if i in eligible_matrix.columns]
            ]

            valid_pairs = int(sub.values.sum())
            total_pairs = n * (n - 1)

            total_vp_all += valid_pairs
            total_tp_all += total_pairs
            # n > 1 guard: single-floor clusters have no pairs by definition.
            # They are already effectively noise — do not double-penalise.
            # Only reclassify multi-floor clusters that fail the time constraint.
            
            if valid_pairs == 0 and n > 1:
                # No physically realizable reuse — demote entire cluster to noise
                df.loc[cluster_mask, "cluster"] = -1
                rho_k_map[k] = 0.0
                continue

            # Reuse coefficient per cluster — Peurifoy & Oberlender (2010)
            # Ch.7: industry benchmark is 60-80% for typical floor clusters.
            # If rho_k < 0.6 for a "typical" cluster, flag it — the schedule
            # may be too spread out for effective panel reuse.
            if total_pairs == 0:
                rho_k = 0.0
            else:
                rho_k = valid_pairs / total_pairs

            rho_k_map[k] = rho_k

            # Build reuse-pair rows for the UI table
            for i in cluster_ids:
                for j in cluster_ids:
                    if i == j:
                        continue
                    if i not in eligible_matrix.index or j not in eligible_matrix.columns:
                        continue
                    if eligible_matrix.at[i, j]:
                        sw_i = df.loc[df[id_col] == i, "strip_week"].iloc[0]
                        ws_j = df.loc[df[id_col] == j, "week_start"].iloc[0]
                        reuse_pairs.append({
                            "Cluster": k,
                            "From Floor": i,
                            "To Floor": j,
                            "Panels freed (week)": int(sw_i),
                            "Needed by (week)": int(ws_j),
                            "Weeks buffer": int(ws_j - sw_i - transport_weeks),
                        })

        # Warn on clusters whose rho_k is below the 60% benchmark
        for k, rho in rho_k_map.items():
            if rho < 0.6 and rho > 0.0:
                _warn(
                    f"Cluster {k}: reuse coefficient {rho:.0%} is below the "
                    "60% industry benchmark (Peurifoy & Oberlender, 2010). "
                    "Schedule floors closer together to improve reuse."
                )

    else:
        # No schedule columns — skip eligibility; use legacy rho_k = 0
        unique_clusters = [k for k in df["cluster"].unique() if k != -1]
        for k in unique_clusters:
            n = (df["cluster"] == k).sum()
            rho_k_map[k] = 0.0

    # ── Assign rho_k per floor ────────────────────────────────────────────
    df["rho_k"] = df["cluster"].map(lambda c: rho_k_map.get(c, 0.0))

    # ── Overall reuse rate ────────────────────────────────────────────────
    if total_tp_all > 0:
        overall_reuse = total_vp_all / total_tp_all
    else:
        overall_reuse = 0.0

    # ── Repetition score (% of floors in dominant non-noise cluster) ──────
    floor_type_col = "floor_type" if "floor_type" in df.columns else None
    if floor_type_col:
        typical_mask  = df[floor_type_col] == "Typical"
        typical_floors = df[typical_mask]
        if len(typical_floors) > 0:
            best_cluster = typical_floors["cluster"].value_counts().index[0]
            in_cluster   = (df["cluster"] == best_cluster).sum()
        else:
            in_cluster = (df["cluster"] == 0).sum()
    else:
        non_noise = df[df["cluster"] != -1]
        if len(non_noise) > 0:
            best_cluster = non_noise["cluster"].value_counts().index[0]
            in_cluster   = (df["cluster"] == best_cluster).sum()
        else:
            in_cluster = 0

    repetition_score = round((in_cluster / len(df)) * 100, 1)

    # ── Cluster summary ───────────────────────────────────────────────────
    agg_map = {
        "count": (id_col, "count"),
        "avg_slab": (area_col, "mean"),
        "avg_wall": (wall_col, "mean"),
    }
    cluster_summary = df.groupby("cluster").agg(**agg_map).reset_index()

    # ── Kit Families ──────────────────────────────────────────────────────
    kit_families = generate_kit_families(df, df["cluster"].values)

    return df, repetition_score, cluster_summary, rho_k_map, reuse_pairs, overall_reuse, kit_families
