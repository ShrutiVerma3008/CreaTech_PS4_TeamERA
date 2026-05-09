# FormOptiX — The Developer's Guide 💻

Welcome to the technical documentation for FormOptiX. If you are a Data Scientist, Software Engineer, or Technical Evaluator looking to understand the mechanics, validate our architecture, or extend the codebase, you are in the right place.

---

## 🏗️ Architecture & Design Philosophy

FormOptiX is built using a strict **Separation of Concerns** (Clean Architecture) pattern. 
We explicitly decouple the heavy mathematical lifting from the User Interface.

- **`backend/` is a strict no-Streamlit zone.** Every module here relies on pure Python, NumPy, Pandas, and Scikit-Learn. It raises standard Python exceptions (`ValueError`) instead of UI-specific errors (`st.error`). This means the entire FormOptiX engine can be easily extracted and deployed as an enterprise REST API (e.g., using FastAPI) or integrated directly into SAP/ERP systems.
- **`frontend/` contains zero business logic.** The UI layer only parses user inputs, calls the backend engine, and renders the results via Plotly charts and Streamlit components.

### Project Structure Tree

```text
FormOptiX/
├── backend/                  
│   ├── core/
│   │   ├── clustering.py     # DBSCAN clustering & Kit BOM generation
│   │   ├── lp_optimizer.py   # SKU-level LP BoQ optimizer (PuLP/CBC)
│   │   ├── freeze_guard.py   # Design Freeze Intelligence (DI index calculation)
│   │   └── cross_site.py     # Greedy matching algorithm for portfolio reallocation
│   └── utils/
│       ├── data_loader.py    # Excel validation & column mapping
│       ├── demand_calc.py    # Building the physical reuse eligibility matrix
│       ├── synthetic_data.py # Deterministic building data & Prophet-style forecasting
│       └── report_generator.py # PDF BoQ report generation (ReportLab)
│
├── frontend/                 
│   ├── app.py                # Main Streamlit router and state orchestrator
│   ├── theme.py              # Centralized CSS, color tokens, and Plotly theme logic
│   ├── charts.py             # All Plotly `go.Figure` builders (independently testable)
│   └── pages/                # Individual UI tab renderers (e.g., repetition.py, portfolio.py)
│
├── tests/                    # Robust pytest suite
├── data/                     # Sample Excel datasets
└── docs/                     # Documentation assets
```

---

## ⚙️ Core Algorithms

### 1. Repetition Clustering (`backend/core/clustering.py`)
We use **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)** instead of K-Means.
- **Why?** K-Means forces all floors into a cluster. In construction, you often have a massive podium (noise) and standard tower floors. DBSCAN perfectly isolates the "Typical" floors while naturally classifying the podium and amenities as outliers (`cluster = -1`), preventing them from skewing the standard Kit BOM.

### 2. Formwork LP Optimizer (`backend/core/lp_optimizer.py`)
We model procurement as an **Integer Linear Programming (ILP)** problem using the `PuLP` library.
- **Objective:** Minimize $\sum (C_p \cdot X_t) + \sum (C_h \cdot I_t)$
  *(Minimize Procurement Cost + Holding Cost)*
- **Constraints:** 
  - $I_t \geq D_t$ (Inventory must meet weekly Demand)
  - Flow balance: $I_t = I_{t-1} + X_t$
- **Solver:** Default CBC (Coin-or branch and cut).

### 3. Design Freeze Intelligence (`backend/core/freeze_guard.py`)
Calculates a **Design Instability (DI)** index based on the Coefficient of Variation (CV) of floor geometries across recent revisions. If $DI > 15\%$, the system flags a `HALT` on procurement, preventing scrap generation from premature ordering.

### 4. Cross-Site Reallocation (`backend/core/cross_site.py`)
Uses a **Greedy First-Fit Algorithm** to match idle inventory pools at `Site A` to upcoming procurement demands at `Site B`, respecting physical transport lead times.

---

## 🛠️ How to Extend the Codebase

### Adding a New Algorithm
If you want to replace our DBSCAN with a novel Graph-based clustering approach:
1. Create `backend/core/graph_clustering.py`.
2. Ensure your function takes a `pd.DataFrame` and returns the expected tuple signature.
3. Update `frontend/app.py` to import and call your new function instead of `compute_repetition_score`.

### Modifying the UI
- **Need a new chart?** Add the raw Plotly builder to `frontend/charts.py`. Do NOT put `st.plotly_chart` inside the builder function. Return the `go.Figure` and let the page modules handle rendering.
- **Need a new Tab?** Create `frontend/pages/my_new_tab.py` with a `def render(state: dict):` function, and register it in `frontend/app.py` under the "Tab routing" section.

---

## 🧪 Testing

We take reliability seriously. The `tests/` directory contains **30 automated tests** covering data validation, edge cases in the freeze guard, deterministic synthetic data generation, and cross-site logic.

To run the suite:
```bash
python3 -m pytest tests/ -v
```

### Writing New Tests
All tests use `pytest`. When adding new backend logic, create a corresponding `test_*.py` file in the `tests/` directory. Use `@pytest.fixture` to generate mock Pandas DataFrames to simulate construction geometries.

---

## 📦 Dependency Management

The project relies heavily on the SciPy/PyData stack:
- `pandas` & `numpy`: Core data manipulation.
- `scikit-learn`: For the DBSCAN implementation.
- `pulp`: The mathematical optimization engine.
- `plotly` & `streamlit`: For the reactive, data-dense UI.

Install the exact environment using:
```bash
pip install -r requirements.txt
```
