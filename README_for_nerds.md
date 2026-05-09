# FormOptiX — The Developer's Guide 💻

*For domain experts and judges, see [README.md](README.md).*

Welcome to the technical documentation for FormOptiX. This guide is intended for Data Scientists, Software Engineers, and Technical Evaluators who want to understand the code mechanics, validate the architecture, reproduce results, or build on top of the codebase.

---

## 🏗️ Architecture & Design Philosophy

FormOptiX is built using a strict **Separation of Concerns** (Clean Architecture) pattern. The heavy algorithmic logic is completely decoupled from the User Interface layer.

### The Core Principle: Backend is a Streamlit-free zone

Every module inside `backend/` follows these rules:
1. **No `import streamlit`** — ever. Violations break testability and ERP integratability.
2. **Raise standard exceptions.** Functions raise `ValueError` with descriptive messages instead of calling `st.error()`. The frontend catches and displays them.
3. **Pure data in, pure data out.** All functions accept `pd.DataFrame` / plain Python dicts/lists and return the same. No side effects.

This means the entire FormOptiX computation engine can be:
- Deployed as a **FastAPI REST endpoint** in under 30 minutes.
- Plugged into **SAP/ERP** via a Python adapter without touching the algorithm code.
- Called from a **Jupyter Notebook** for research or validation.

### Data Flow Diagram

```
User Input (Sidebar/Upload)
        │
        ▼
frontend/app.py  ──────────────────────────────────────────┐
   │  (Orchestrator: reads inputs, calls backend, stores     │
   │   results in st.session_state, routes to tab pages)     │
   │                                                         │
   ├──► backend/utils/synthetic_data.py  (demo mode)         │
   │    └──► returns (df_floors, df_schedule)                │
   │                                                         │
   ├──► backend/utils/data_loader.py  (real mode)            │
   │    └──► validate_and_map() ─► raises ValueError on bad │
   │                                data; frontend catches   │
   │                                                         │
   ├──► backend/core/freeze_guard.py                         │
   │    └──► compute_design_freeze(df_floors) ─► DI index    │
   │                                                         │
   ├──► backend/core/clustering.py                           │
   │    └──► compute_repetition_score() ─► (df, score,      │
   │         cluster_summary, rho_k_map, reuse_pairs,        │
   │         overall_reuse)                                  │
   │    └──► generate_kit_bom(cluster_summary) ─► dict      │
   │                                                         │
   ├──► backend/core/lp_optimizer.py                         │
   │    └──► run_sku_optimizer() ─► {status, boq_results,   │
   │         savings, trad_total, opt_total, chart arrays}   │
   │                                                         │
   └──► frontend/pages/*.py  (render results, no computation)│
         └──► frontend/charts.py  (return go.Figure only)    │
                                                             │
        st.session_state (shared state dict) ───────────────┘
```

---

## 📁 Project Structure (Annotated)

```text
FormOptiX/
│
├── backend/                        # Pure Python. Zero Streamlit.
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py             # Exports: compute_repetition_score, run_sku_optimizer,
│   │   │                           #          compute_design_freeze, collect_idle_panels,
│   │   │                           #          match_supply_to_demand, generate_kit_bom
│   │   ├── clustering.py           # DBSCAN + physical reuse filter + Kit BOM
│   │   ├── lp_optimizer.py         # PuLP ILP formulation (3 SKUs, 52 weeks)
│   │   ├── freeze_guard.py         # DI index (CV-based) + procurement recommendation
│   │   └── cross_site.py           # Greedy first-fit cross-site panel matching
│   └── utils/
│       ├── __init__.py             # Lazy-imports report_generator to avoid reportlab dep
│       ├── data_loader.py          # validate_and_map() — Excel ingest + validation
│       ├── demand_calc.py          # build_reuse_matrix() — eligibility matrix
│       ├── synthetic_data.py       # generate_building_data() + simulate_forecast()
│       └── report_generator.py     # generate_boq_pdf() — requires reportlab
│
├── frontend/
│   ├── app.py                      # st.set_page_config → sidebar → engine → tabs
│   ├── theme.py                    # CSS injection, color constants, apply_chart_theme()
│   ├── charts.py                   # All go.Figure builders. No st.* calls inside.
│   └── pages/
│       ├── __init__.py
│       ├── repetition.py           # Tab 1: gauge, cluster chart, Kit BOM, DFI
│       ├── cost.py                 # Tab 2: ROI counter, LP detail table, waterfall
│       ├── inventory.py            # Tab 3: inventory curve, forecast, PDF export
│       ├── building_data.py        # Tab 4: donut, scatter, floor data table
│       ├── roadmap.py              # Tab 5: phase cards, impact table, competitive chart
│       └── portfolio.py            # Tab 6: cross-site reallocation matcher
│
├── tests/
│   ├── __init__.py
│   ├── test_clustering.py          # (run pytest to see 30 passing tests)
│   ├── test_cross_site.py
│   ├── test_data_loader.py
│   ├── test_freeze_guard.py
│   └── test_synthetic_data.py
│
├── data/
│   ├── demo_tower_40floors.xlsx
│   ├── formoptix_real_project.xlsx
│   └── sample_project.xlsx
│
├── docs/assets/
├── requirements.txt
├── README.md                       # Domain Expert guide
└── README_for_nerds.md             # This file
```

---

## ⚙️ Core Algorithms — Deep Dive

### 1. Repetition Clustering — `backend/core/clustering.py`

**Why DBSCAN over K-Means?**

K-Means requires you to pre-specify `k` (the number of clusters) and forces every data point into a cluster. In construction, a 40-floor tower typically has:
- 2–3 podium floors (unique geometry)
- 1–2 mechanical plant floors (unique)
- 28–30 "Typical" floors (nearly identical)
- 1–2 terrace/penthouse floors (unique)

DBSCAN handles this naturally. It finds the dense region (typical floors) and labels everything outside it as `cluster = -1` (noise/outlier). This means our Repetition Score and Kit BOM are never corrupted by outlier geometries.

**Feature Space:**
```python
features = [slab_area_sqm, wall_length_m, column_count, beam_count]
```
All features are StandardScaler-normalized before DBSCAN to prevent area (large numbers) from dominating over column count (small numbers).

**DBSCAN Hyperparameters:**
```python
DBSCAN(eps=0.8, min_samples=2)
```
- `eps=0.8` in normalized space corresponds to ~5% geometric variation between "similar" floors.
- `min_samples=2` means any two similar floors form a valid cluster (appropriate for small buildings; can be tuned up for tall towers).

**Physical Reuse Filter (Post-DBSCAN):**
DBSCAN tells us which floors are *geometrically* similar, but that doesn't mean the panels are *physically available* to transfer. We apply a second pass using a **reuse eligibility matrix** from `demand_calc.py`:

```python
# A panel from floor i can be reused on floor j if:
strip_week[i] + transport_weeks <= week_start[j]
```
This is directly derived from **ACI 347R-14 Section 5** (minimum stripping times) and **Hanna (1998) Ch.4** (transport logistics).

If a cluster has zero physically valid reuse pairs, it is reclassified as noise (`-1`). This prevents the optimizer from counting reuse that isn't physically achievable.

**Reuse Coefficient (ρ_k):**
```
ρ_k = valid_reuse_pairs / total_possible_pairs_in_cluster
```
The industry benchmark is ≥60% (Peurifoy & Oberlender, 2010, Ch.7). Clusters below 60% generate a `warnings.warn()` to be surfaced by the UI.

---

### 2. Kit BOM Generator — `backend/core/clustering.py:generate_kit_bom()`

Takes the dominant cluster's average geometry and translates it into a physical panel count using standard industry panel dimensions:

```python
wall_panels_600mm       = int(avg_wall_length  / 0.6)
slab_panels_1500x1000   = int(avg_slab_area    / 1.5)
col_panels_standard     = int(avg_column_count * 4)
```

Panel sizing conventions follow standard aluminium formwork specifications used by L&T and MIVAN systems.

---

### 3. LP BoQ Optimizer — `backend/core/lp_optimizer.py`

**Model Formulation:**

We solve three independent LP subproblems (one per SKU: wall, slab, column) using PuLP with the CBC solver.

**Decision Variables (per week `t`):**
- `x[t]` — panels procured fresh this week (≥ 0)
- `h[t]` — panels held in inventory from previous weeks (≥ 0)
- `i[t]` — idle panels (unused, sitting in yard) (≥ 0)

**Objective:**
```
Minimize: Σ(c_p × x[t]) + Σ(c_h × h[t]) + Σ(c_i × i[t])
```
Where:
- `c_p` = procurement cost per panel (default ₹15,000)
- `c_h` = holding/rental cost per panel per week (default ₹500)
- `c_i` = idle penalty per panel per week (default ₹800)

**Constraints:**

| ID | Constraint | Meaning |
|----|-----------|---------|
| C1 | `x[t] + reuse[t] + h[t-1] ≥ demand[t]` | Inventory must always meet demand |
| C2 | `h[t] = (x[t] + reuse[t] + h[t-1]) - demand[t]` | Inventory balance / flow conservation |
| C3 | `x[t] ≤ total_demand_sku` | Purchase cap to prevent unbounded buying |

**Solver:** CBC (Coin-or Branch and Cut) via PuLP. Academic reference: Forrest & Lougee-Heimer (2005).

**Fallback:** If PuLP is not installed, the system falls back to a Just-In-Time (JIT) heuristic that procures exactly `max(0, demand - reuse)` each week with no carry-forward.

**Baseline for Comparison:**
The "traditional" baseline is computed as:
```python
baseline = c_p × Σ(demand_w) × 1.20   # 20% buffer assumption (industry norm)
```

---

### 4. Design Freeze Intelligence — `backend/core/freeze_guard.py`

**Design Instability (DI) Index:**
```python
CV_slab  = std(slab_area)  / mean(slab_area)
CV_wall  = std(wall_length) / mean(wall_length)
CV_col   = std(col_count)  / mean(col_count)
DI = (CV_slab + CV_wall + CV_col) / 3 * 100   # percentage
```

The 15% threshold is derived from **Ibbs (1997)**: projects with design variation above this threshold statistically show >60% higher rework rates.

**Procurement Status Logic:**
| DI Value | Status | Action |
|----------|--------|--------|
| DI < 10% | `SAFE` | Full procurement authorized |
| 10% ≤ DI < 15% | `WARNING` | Proceed with caution; delay bulk orders |
| DI ≥ 15% | `HALT` | Block all procurement; alert project manager |

**Outlier Detection for Unstable Floors:**
Uses the **MAD (Median Absolute Deviation)** method (Leys et al., 2013) to identify specific floors driving instability:
```python
MAD = median(|x - median(x)|)
outlier if |x - median(x)| > 2.5 * MAD
```
MAD is preferred over z-score because it is robust to the very outliers we are trying to detect.

---

### 5. Cross-Site Reallocation — `backend/core/cross_site.py`

**Algorithm: Greedy First-Fit**

```python
for each demand_row (site_B, sku, week_needed, qty):
    for each idle_row in idle_pool:
        if (idle_row.sku == demand_row.sku
            and idle_row.site != demand_row.site      # different site
            and idle_row.week <= demand_row.week - 1  # available in time
            and idle_row.idle_qty >= demand_row.qty): # enough panels
                → CREATE MATCH
                → REDUCE idle_pool to prevent double-allocation
                → BREAK (first-fit)
```

**Note:** The greedy first-fit is not optimal. A full cross-site LP (Biruk & Jaskowski, 2017) would be optimal but was deferred as out-of-scope for Phase 0. The current implementation provides good practical results while being O(n×m) and explainable to site engineers.

---

## 🛠️ How to Extend the Codebase

### Adding a New Clustering Algorithm

1. Create `backend/core/your_algorithm.py`.
2. Your main function must match this signature:
   ```python
   def compute_repetition_score(
       df_floors: pd.DataFrame,
       transport_weeks: int = 1,
   ) -> tuple:
       # Returns: (df_floors_with_clusters, repetition_score, cluster_summary,
       #           rho_k_map, reuse_pairs, overall_reuse)
   ```
3. In `frontend/app.py`, swap the import:
   ```python
   # from backend.core.clustering import compute_repetition_score
   from backend.core.your_algorithm import compute_repetition_score
   ```
4. Write tests in `tests/test_your_algorithm.py`. The `tests/test_clustering.py` file is a good template.

### Adding a New Frontend Tab

1. Create `frontend/pages/my_tab.py` with exactly this structure:
   ```python
   import streamlit as st

   def render(state: dict) -> None:
       """All keys in `state` are documented in frontend/app.py:shared dict."""
       my_data = state["my_key"]
       st.write(my_data)
   ```
2. In `frontend/app.py`, add the import and routing:
   ```python
   import frontend.pages.my_tab as pg_my_tab
   # ...
   tab1, ..., tab_new = st.tabs([..., "🆕 My New Tab"])
   with tab_new: pg_my_tab.render(shared)
   ```

### Adding a New Chart

1. Add the builder to `frontend/charts.py`:
   ```python
   def make_my_chart(data: pd.DataFrame) -> go.Figure:
       fig = go.Figure(...)
       return apply_chart_theme(fig, "My Chart Title", height=350)
   ```
2. Call it from a page module:
   ```python
   from frontend.charts import make_my_chart
   st.plotly_chart(make_my_chart(df), use_container_width=True)
   ```
   **Never** put `st.plotly_chart()` inside the chart builder. The builder must be a pure function: data in, `go.Figure` out.

---

## 🧪 Testing

### Running Tests
```bash
python3 -m pytest tests/ -v
```

All **30 tests pass** on a clean install:

```
tests/test_cross_site.py::test_collect_idle_filters_zero        PASSED
tests/test_cross_site.py::test_match_finds_cross_site           PASSED
tests/test_cross_site.py::test_match_same_site_not_matched      PASSED
tests/test_cross_site.py::test_match_timing_constraint          PASSED
tests/test_cross_site.py::test_match_does_not_double_allocate   PASSED
tests/test_data_loader.py::test_valid_data_passes               PASSED
tests/test_data_loader.py::test_missing_required_column_raises  PASSED
tests/test_data_loader.py::test_duplicate_floor_id_raises       PASSED
tests/test_data_loader.py::test_strip_before_end_raises         PASSED
tests/test_data_loader.py::test_non_positive_area_raises        PASSED
tests/test_freeze_guard.py::test_stable_is_safe                 PASSED
tests/test_freeze_guard.py::test_unstable_is_halt               PASSED
tests/test_freeze_guard.py::test_accepts_alternate_col_names    PASSED
tests/test_synthetic_data.py::test_generate_correct_row_count   PASSED
tests/test_synthetic_data.py::test_generate_deterministic       PASSED
... (30 total)
```

### Test Design Principles
- **No Streamlit mocking required.** Because the backend is pure Python, tests import and call functions directly — no `@st.cache_data` or `MagicMock` needed.
- **Fixtures generate minimal DataFrames.** `@pytest.fixture` creates small (10–20 row) DataFrames that exercise boundary conditions (zero clusters, zero idle panels, etc.) without slow data generation.
- **Deterministic seeds.** All tests that involve randomness use `np.random.seed(0)` for reproducibility.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | ≥1.32 | Interactive web UI |
| `plotly` | ≥5.18 | Charting (all charts are `go.Figure` objects) |
| `pandas` | ≥2.0 | DataFrame manipulation |
| `numpy` | ≥1.26 | Numerical operations |
| `scikit-learn` | ≥1.4 | DBSCAN implementation |
| `scipy` | ≥1.12 | Statistical functions (MAD, CV) |
| `pulp` | ≥2.7 | LP/ILP solver (CBC backend) |
| `openpyxl` | ≥3.1 | Excel file read/write |
| `reportlab` | ≥4.0 | **Optional** — PDF BoQ export |

Install everything (except reportlab):
```bash
pip install -r requirements.txt
```

Install with PDF support:
```bash
pip install -r requirements.txt reportlab
```

### Handling Missing Dependencies
Both `sklearn` and `pulp` are optional at the algorithm level:
- If `sklearn` is missing → falls back to a manual distance-based grouping heuristic.
- If `pulp` is missing → falls back to a Just-In-Time (JIT) heuristic.
- If `reportlab` is missing → PDF export button is hidden; all other functionality works normally.

---

## 🔑 Key Design Decisions & Their Rationale

| Decision | Alternative Considered | Why We Chose This |
|----------|----------------------|-------------------|
| DBSCAN for clustering | K-Means | DBSCAN handles noise natively; no need to pre-specify `k` |
| PuLP/CBC for LP | Google OR-Tools, Gurobi | CBC is license-free; PuLP is Pythonic; OR-Tools was overkill |
| Greedy first-fit for cross-site | Full ILP across sites | Simpler to explain to engineers; Phase 0 prototype |
| `ValueError` in backend instead of `st.error` | Streamlit error calls | Enables unit testing; decouples UI from logic |
| Lazy import for `reportlab` in `__init__.py` | Direct import | Avoids hard dependency crash for users without reportlab |
| `st.session_state` for shared state | URL params / database | Appropriate for single-user prototype; scalable to Redis in Phase 1 |

---

## 📚 Academic References

All citations are inline in the source code. Consolidated list:

1. Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. *KDD-96*. AAAI Press.
2. Hillier, F.S., & Lieberman, G.J. (2021). *Introduction to Operations Research* (11th ed.). McGraw-Hill.
3. Hanna, A.S. (1998). *Concrete Formwork Systems*. Marcel Dekker.
4. ACI Committee 347. (2014). *ACI 347R-14: Guide to Formwork for Concrete*. American Concrete Institute.
5. Ibbs, C.W. (1997). Quantitative impacts of project change. *Journal of Construction Engineering and Management*, 123(3), 308–311.
6. Peurifoy, R.L., & Oberlender, G.D. (2010). *Formwork for Concrete Structures* (4th ed.). McGraw-Hill.
7. Dania, A.A., Fulford, R., & Hassanain, M.A. (2015). Performance evaluation of formwork systems. *Journal of Engineering, Design and Technology*, 13(3).
8. Forrest, J., & Lougee-Heimer, R. (2005). CBC user guide. *INFORMS*.
9. Leys, C., et al. (2013). Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median. *Journal of Experimental Social Psychology*, 49(4).
10. Mitchell, S., O'Sullivan, M., & Dunning, I. (2011). *PuLP: A linear programming toolkit for Python*. University of Auckland.
