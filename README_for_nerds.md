# FormOptiX — Technical Architecture & Developer Documentation

*For the comprehensive business case and high-level overview, please refer to the primary [README.md](README.md).*

This document provides a detailed technical exposition of the FormOptiX engine. It is intended for software engineers, data scientists, and technical evaluation committees to understand the underlying system architecture, mathematical models, algorithms, and guidelines for extending the codebase.

---

## 🏗️ System Architecture (Separation of Concerns)

FormOptiX implements a rigorous **Separation of Concerns** based on Clean Architecture principles. The mathematical models and optimization engines are entirely decoupled from the User Interface (UI), ensuring high maintainability and system interoperability.

### Core Architectural Directives: Backend Isolation

Within the `backend/` directory, several strict conventions are maintained:
1. **No UI Dependencies:** The Streamlit library (`import streamlit`) is strictly prohibited in the backend. This ensures the core logic can be seamlessly integrated into Enterprise Resource Planning (ERP) systems (e.g., SAP) or deployed as independent microservices.
2. **Standardized Exception Handling:** Backend functions raise standard Python exceptions (e.g., `ValueError`) with descriptive messages, rather than utilizing UI-specific error functions. The frontend layer is responsible for catching and displaying these appropriately.
3. **Pure Functions and Standard Data Structures:** The backend operates exclusively on standard data structures (Pandas DataFrames, lists, dictionaries). It ensures deterministic behavior without UI side effects.

**Implications of this Architecture:**
- The backend can be immediately wrapped in a framework like FastAPI to expose RESTful endpoints.
- The optimization engine can be embedded into existing enterprise software.
- Research iterations can be performed locally within Jupyter Notebook environments without UI overhead.

### Data Flow Overview

```text
User Input (Sidebar/File Upload)
        │
        ▼
[Frontend Controller: frontend/app.py]
   │  (Manages inputs, invokes backend processes,
   │   maintains st.session_state, handles routing)
   │
   ├──► [Data Ingestion] backend/utils/data_loader.py 
   │    └──► validate_and_map() ─► Validates schema and maps custom columns
   │
   ├──► [Risk Modeling] backend/core/freeze_guard.py
   │    └──► compute_design_freeze(df) ─► Returns Design Instability (DI) metrics
   │
   ├──► [Pattern Recognition] backend/core/clustering.py
   │    └──► compute_repetition_score() ─► Outputs clusters, scores, reuse feasibility
   │    └──► generate_kit_bom() ─► Calculates optimized Bill of Materials
   │
   ├──► [Financial Optimization] backend/core/lp_optimizer.py
   │    └──► run_sku_optimizer() ─► Solves ILP, returns procurement schedule and savings
   │
   └──► [UI Rendering] frontend/pages/*.py 
         └──► frontend/charts.py (Constructs Plotly figures based on backend output)
```

---

## 📁 Repository Structure

```text
FormOptiX/
│
├── backend/                        # Core algorithms, data processing, and mathematical models
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py             # Public API exports for core functions
│   │   ├── clustering.py           # DBSCAN implementation, physical reuse constraints, BOM generation
│   │   ├── lp_optimizer.py         # PuLP Integer Linear Programming solver (52-week horizon)
│   │   ├── freeze_guard.py         # Design Instability (DI) index calculation
│   │   └── cross_site.py           # Greedy algorithm for inter-site inventory reallocation
│   └── utils/
│       ├── __init__.py             # Lazy loading configuration for optional dependencies (e.g., reportlab)
│       ├── data_loader.py          # Input validation, sanitization, and schema mapping
│       ├── demand_calc.py          # Derivation of formwork demand based on geometric data
│       ├── synthetic_data.py       # Deterministic generation of test structures and forecast data
│       └── report_generator.py     # Automated generation of PDF Bill of Quantities reports
│
├── frontend/                       # User Interface and Presentation Layer
│   ├── app.py                      # Application entry point and navigation controller
│   ├── theme.py                    # Centralized styling configuration and UI themes
│   ├── charts.py                   # Decoupled visualization functions returning Plotly figures
│   └── pages/
│       ├── __init__.py
│       ├── repetition.py           # Tab 1: Clustering visualization, Kit BOM, and DI Index
│       ├── cost.py                 # Tab 2: Financial models, ROI metrics, and waterfall charts
│       ├── inventory.py            # Tab 3: Inventory forecasting and temporal demand curves
│       ├── building_data.py        # Tab 4: Raw dataset inspection and scatter matrix analysis
│       ├── roadmap.py              # Tab 5: Strategic deployment phases and competitive analysis
│       └── portfolio.py            # Tab 6: Multi-site inventory reallocation simulation
│
├── tests/                          # Automated testing suite
│   ├── __init__.py
│   ├── test_clustering.py          
│   ├── test_cross_site.py
│   ├── test_data_loader.py
│   ├── test_freeze_guard.py
│   └── test_synthetic_data.py
│
├── data/                           # Sample datasets for evaluation
│   ├── demo_tower_40floors.xlsx
│   ├── formoptix_real_project.xlsx
│   └── sample_project.xlsx
│
├── docs/assets/                    # Documentation imagery and static assets
├── requirements.txt                # Dependency manifest
├── README.md                       # Executive summary and business case
└── README_for_nerds.md             # Technical and architectural documentation
```

---

## ⚙️ Algorithmic Implementations

### 1. Repetition Clustering (`backend/core/clustering.py`)

**Algorithmic Selection: DBSCAN vs. K-Means**
Traditional clustering approaches, such as K-Means, rigidly assign every data point to a predefined number of clusters. In architectural datasets, buildings exhibit "typical" floors alongside highly irregular "unique" floors (e.g., podiums, mechanical levels). 

We implemented **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)** because it intrinsically isolates these anomalies. DBSCAN aggregates the dense grouping of typical floors while categorizing irregular geometries as noise (`cluster = -1`). This ensures the Repetition Score and standard Kit BOM are derived solely from standard configurations, preventing statistical skewing from structural anomalies.

**Physical Reuse Constraints:**
Geometric similarity is necessary but not sufficient for formwork reuse. The system applies a secondary temporal filter derived from construction physics and the **ACI 347R-14 guidelines** for concrete curing:

```python
# Reusability Constraint:
# Panel transfer from Floor A to Floor B is only feasible if:
strip_week[Floor A] + transport_duration <= pour_week[Floor B]
```
If a geometrically clustered set of floors violates these temporal constraints, the cluster is fragmented or disqualified, ensuring the optimizer only works with physically executable schedules.

---

### 2. Kit Bill of Materials (BOM) Generation (`generate_kit_bom()`)

Following the identification of the primary repetitive cluster, the system synthesizes an optimized BOM. It computes the mean geometric parameters of the cluster and translates these into a standardized aluminum formwork inventory requirement:

```python
# Simplistic representation of BOM generation logic:
wall_panels_600mm       = int(average_wall_length  / 0.6)
slab_panels_1500x1000   = int(average_slab_area    / 1.5)
col_panels_standard     = int(average_column_count * 4)
```

---

### 3. Financial Optimization Engine (`backend/core/lp_optimizer.py`)

Formwork procurement is modeled as an **Integer Linear Programming (ILP)** problem, resolved utilizing the `PuLP` library and the underlying CBC solver. The engine optimizes over a 52-week horizon across distinct Stock Keeping Units (SKUs: walls, slabs, columns).

**Objective Function:**
The mathematical objective is to strictly minimize the total lifecycle cost:
`Minimize: Σ [(Cost_New × Qty_Purchased) + (Holding_Cost × Qty_Retained) + (Penalty_Cost × Qty_Shortfall)]`

**Primary Constraints:**
1. **Demand Satisfaction:** Total available inventory in period $t$ must meet or exceed the projected demand for period $t$.
2. **Inventory Conservation (Flow Balance):** Inventory at $t+1$ equals Inventory at $t$ plus new purchases, minus consumed or degraded units.
3. **Capital Budgeting Constraints:** Upper bounds are placed on weekly procurement volume to prevent front-loaded expenditure.

*Note: In environments lacking the `PuLP` dependency, the system gracefully degrades to a deterministic Just-In-Time (JIT) heuristic solver to ensure uninterrupted operation.*

---

### 4. Design Freeze Intelligence (`backend/core/freeze_guard.py`)

To quantify design stability, the system calculates a **Design Instability (DI) Index** by evaluating the Coefficient of Variation (CV) across successive structural design revisions.

If the DI Index exceeds a critical threshold (`DI > 15%`), the system issues a proactive `HALT` recommendation for procurement. Empirical studies in construction management (e.g., Ibbs, 1997) demonstrate an exponential correlation between design variation above this threshold and subsequent field rework.

The system further utilizes the **Median Absolute Deviation (MAD)** method to identify the specific floors contributing most to the instability, providing robust outlier detection superior to standard deviation.

---

### 5. Multi-Site Reallocation (`backend/core/cross_site.py`)

For portfolio-level optimization, matching idle inventory at one site to impending demand at another site is managed via a **Greedy First-Fit Algorithm**. The algorithm chronologically evaluates demand spikes and searches the regional pool of idle panels capable of meeting logistical transit timelines.

While a comprehensive multi-site ILP model would yield absolute mathematical optimality, this $O(n \times m)$ approach provides highly efficient, near-optimal solutions that execute rapidly and offer transparent logic for validation by site engineers.

---

## 🛠️ Extensibility and Integration

### Integrating Novel Clustering Models
To implement alternative statistical or machine learning models for geometric grouping:
1. Develop the algorithm in a new module within `backend/core/` (e.g., `advanced_clustering.py`).
2. Ensure the primary function accepts a standardized DataFrame and outputs the predefined tuple signature required by the application state.
3. Update the invocation in `frontend/app.py` to route data through the new module.

### Expanding User Interface Capabilities
The modular frontend structure simplifies expansion:
1. Initialize a new file within `frontend/pages/` (e.g., `analytics_tab.py`).
2. Define a `render(state: dict)` function. The `state` parameter injects the globally computed application context.
3. Register the new tab within the `st.tabs()` instantiation in `frontend/app.py` and invoke its `render()` function.

### Adding Visualizations
1. Construct the Plotly figure logic within `frontend/charts.py`. (Ensure the function returns a `go.Figure` object to maintain UI decoupling).
2. Import and invoke this builder function within the relevant `frontend/pages/` module to display the chart.

---

## 🧪 Testing Methodology

The repository incorporates an automated testing suite comprising **30 individual tests** designed to validate algorithmic integrity, mathematical correctness, and edge-case handling.

To execute the test suite, run:
```bash
python3 -m pytest tests/ -v
```

**Testing Principles:**
- **UI Independence:** Because the backend is strictly decoupled, tests instantiate functions directly using predefined DataFrames, eliminating the need for complex Streamlit UI mocking.
- **Fixture Utilization:** `@pytest.fixture` decorators are heavily utilized to generate deterministic, constrained DataFrames to evaluate boundary conditions (e.g., zero-demand scenarios, missing data).
- **Determinism:** Random number generation is explicitly seeded (`np.random.seed(0)`) to ensure reproducible test outcomes across environments.

---

## 📦 Technical Dependencies

The application relies on the following core libraries:

| Library | Function |
|---------|-------------|
| `streamlit` | Reactive web application framework for the frontend interface. |
| `plotly` | High-performance interactive data visualization. |
| `pandas` & `numpy` | Vectorized data manipulation, transformation, and numerical computing. |
| `scikit-learn` | Implementation of the DBSCAN machine learning algorithm. |
| `scipy` | Advanced statistical computations (e.g., MAD and CV metrics). |
| `pulp` | Algebraic modeling language for Integer Linear Programming. |
| `openpyxl` | Ingestion and parsing of `.xlsx` datasets. |
| `reportlab` | *(Optional)* PDF rendering engine for automated BoQ exports. |

Install dependencies via:
```bash
pip install -r requirements.txt
```

---

## 📚 Academic and Technical References

The mathematical models underpinning FormOptiX are derived from established academic literature in operations research and civil engineering:

1. Ester, M., et al. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. *KDD-96*.
2. Hillier, F.S., & Lieberman, G.J. (2021). *Introduction to Operations Research*. McGraw-Hill.
3. Hanna, A.S. (1998). *Concrete Formwork Systems*. Marcel Dekker.
4. ACI Committee 347. (2014). *ACI 347R-14: Guide to Formwork for Concrete*.
5. Ibbs, C.W. (1997). Quantitative impacts of project change. *Journal of Construction Engineering and Management*.
6. Peurifoy, R.L., & Oberlender, G.D. (2010). *Formwork for Concrete Structures*.
7. Dania, A.A., et al. (2015). Performance evaluation of formwork systems. *Journal of Engineering, Design and Technology*.
8. Forrest, J., & Lougee-Heimer, R. (2005). CBC user guide. *INFORMS*.
9. Leys, C., et al. (2013). Detecting outliers using median absolute deviation. *Journal of Experimental Social Psychology*.
10. Mitchell, S., et al. (2011). *PuLP: A linear programming toolkit for Python*.
