"""
backend/core/clustering.py
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

import warnings
import numpy as np
import pandas as pd

try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from backend.utils.demand_calc import build_reuse_matrix


def compute_repetition_score(
    df_floors: pd.DataFrame,
    transport_weeks: int = 1,
) -> tuple:
    """
    Run DBSCAN on floor geometry, then apply the physical reuse filter.

    Parameters
    ----------
    df_floors : pd.DataFrame
        Floor dataframe. Must contain:
          slab_area_sqm / slab_area_m2, wall_length_m, column_count / col_count,
          beam_count (optional), floor_id, week_start, week_end, strip_week.
        Synthetic-mode data uses slab_area_sqm / column_count / beam_count.
        Real-mode data uses slab_area_m2 / col_count (mapped by validate_and_map).
    transport_weeks : int, default 1
        Time (weeks) to move panels between floors.

    Returns
    -------
    df_floors       : DataFrame with 'cluster' and 'rho_k' columns added.
    repetition_score: float — percentage of floors in the dominant cluster.
    cluster_summary : DataFrame — per-cluster stats.
    rho_k_map       : dict  — {cluster_label: rho_k value}.
    reuse_pairs     : list  — list of dicts for the valid-reuse-pairs table.
    overall_reuse   : float — portfolio-wide reuse rate (0–1).
    """
    # ── Normalise column names for both synthetic and real modes ──────────
    df = df_floors.copy()

    area_col = "slab_area_sqm" if "slab_area_sqm" in df.columns else "slab_area_m2"
    wall_col = "wall_length_m"
    col_col  = "column_count" if "column_count" in df.columns else "col_count"
    beam_col = "beam_count" if "beam_count" in df.columns else None
    id_col   = "floor_id"

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

    rho_k_map    = {}
    reuse_pairs  = []
    total_vp_all = 0
    total_tp_all = 0

    if has_schedule:
        eligible_matrix = build_reuse_matrix(
            df[[id_col, "week_start", "week_end", "strip_week"]], transport_weeks
        )

        unique_clusters = [k for k in df["cluster"].unique() if k != -1]

        for k in unique_clusters:
            cluster_mask = df["cluster"] == k
            cluster_ids  = df.loc[cluster_mask, id_col].tolist()
            n            = len(cluster_ids)

            sub = eligible_matrix.loc[
                [i for i in cluster_ids if i in eligible_matrix.index],
                [i for i in cluster_ids if i in eligible_matrix.columns],
            ]

            valid_pairs = int(sub.values.sum())
            total_pairs = n * (n - 1)

            total_vp_all += valid_pairs
            total_tp_all += total_pairs

            if valid_pairs == 0 and n > 1:
                df.loc[cluster_mask, "cluster"] = -1
                rho_k_map[k] = 0.0
                continue

            rho_k = valid_pairs / total_pairs if total_pairs > 0 else 0.0
            rho_k_map[k] = rho_k

            # Warn if reuse rate is below 60% industry benchmark
            # (Peurifoy & Oberlender, 2010, Ch.7)
            if 0.0 < rho_k < 0.6:
                warnings.warn(
                    f"Cluster {k}: reuse coefficient {rho_k:.0%} is below the "
                    "60% industry benchmark (Peurifoy & Oberlender, 2010). "
                    "Schedule floors closer together to improve reuse.",
                    stacklevel=2,
                )

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
                            "Cluster":             k,
                            "From Floor":          i,
                            "To Floor":            j,
                            "Panels freed (week)": int(sw_i),
                            "Needed by (week)":    int(ws_j),
                            "Weeks buffer":        int(ws_j - sw_i - transport_weeks),
                        })
    else:
        # No schedule columns — skip eligibility; use legacy rho_k = 0
        for k in [k for k in df["cluster"].unique() if k != -1]:
            rho_k_map[k] = 0.0

    # ── Assign rho_k per floor ────────────────────────────────────────────
    df["rho_k"] = df["cluster"].map(lambda c: rho_k_map.get(c, 0.0))

    # ── Overall reuse rate ────────────────────────────────────────────────
    overall_reuse = total_vp_all / total_tp_all if total_tp_all > 0 else 0.0

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
        "count":    (id_col,   "count"),
        "avg_slab": (area_col, "mean"),
        "avg_wall": (wall_col, "mean"),
        "avg_col":  (col_col,  "mean"),
    }
    cluster_summary = df.groupby("cluster").agg(**agg_map).reset_index()

    return df, repetition_score, cluster_summary, rho_k_map, reuse_pairs, overall_reuse


def generate_kit_bom(cluster_summary: pd.DataFrame) -> dict:
    """
    Translates the geometric averages of the dominant non-noise cluster 
    into a physical Kit Bill of Materials (BOM).
    
    Industry standard conversion rules:
    - Wall Panels (0.6m width): wall_length / 0.6
    - Slab Panels (1.5 sqm area): slab_area / 1.5
    - Column Panels: 4 panels per column
    
    Returns
    -------
    dict: The physical kit BOM.
    """
    if cluster_summary.empty:
        return {}

    # Exclude noise (-1) and find cluster with max count
    valid = cluster_summary[cluster_summary["cluster"] != -1]
    if valid.empty:
        return {}
        
    dominant = valid.loc[valid["count"].idxmax()]
    
    wall_len = dominant["avg_wall"]
    slab_area = dominant["avg_slab"]
    col_count = dominant.get("avg_col", 0)
    
    return {
        "cluster_id": int(dominant["cluster"]),
        "floor_count": int(dominant["count"]),
        "wall_panels_600mm": int(wall_len / 0.6),
        "slab_panels_1500x1000": int(slab_area / 1.5),
        "col_panels_standard": int(col_count * 4),
    }
