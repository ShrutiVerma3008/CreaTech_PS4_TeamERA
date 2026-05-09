# FormOptiX 🏗️

**Intelligent Formwork & Bill-of-Quantities Optimizer**
CreaTech '26 · L&T · Problem Statement 4 · #JustLeap

---

## What is FormOptiX?

FormOptiX is an AI-driven engine that minimizes formwork procurement and holding costs in high-rise construction projects by:

1. **Clustering floors by geometric similarity** (DBSCAN) to compute a *Repetition Score*
2. **Running a Linear-Programming BoQ optimizer** (PuLP/CBC) to generate a 52-week procurement plan
3. **Guarding against premature procurement** with the Design Freeze Intelligence module (DI index)
4. **Enabling cross-site panel sharing** to reduce idle inventory across projects

---

## Project Structure

```
FormOptiX/
├── backend/                  # Pure Python — no Streamlit anywhere
│   ├── core/
│   │   ├── clustering.py     # DBSCAN repetition clustering
│   │   ├── lp_optimizer.py   # SKU-level LP BoQ optimizer (PuLP/CBC)
│   │   ├── freeze_guard.py   # Design Freeze Intelligence (DI index)
│   │   └── cross_site.py     # Cross-site panel reallocation
│   └── utils/
│       ├── data_loader.py    # Excel validation & column mapping
│       ├── demand_calc.py    # Reuse eligibility matrix
│       ├── synthetic_data.py # Building data generator & forecast
│       └── report_generator.py # PDF BoQ report (requires reportlab)
│
├── frontend/                 # Streamlit UI — calls backend, renders results
│   ├── app.py                # Main entry point
│   ├── theme.py              # CSS + color tokens + chart theme
│   ├── charts.py             # All Plotly chart builders
│   └── pages/
│       ├── repetition.py     # Tab 1 — Repetition Analysis
│       ├── cost.py           # Tab 2 — Cost Optimization
│       ├── inventory.py      # Tab 3 — Inventory & Forecast
│       ├── building_data.py  # Tab 4 — Building Data
│       └── roadmap.py        # Tab 5 — Roadmap & Impact
│
├── tests/                    # pytest test suite (30 tests)
│   ├── test_freeze_guard.py
│   ├── test_data_loader.py
│   ├── test_cross_site.py
│   └── test_synthetic_data.py
│
├── data/                     # Sample Excel project files
├── docs/                     # Documentation & assets
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> Optional: `pip install reportlab` to enable PDF BoQ export.

### 2. Run the app

```bash
streamlit run frontend/app.py
```

The app auto-runs in **Synthetic Demo** mode on first load. Switch to **Real Site Data** in the sidebar to upload your own Excel file.

### 3. Run the tests

```bash
python3 -m pytest tests/ -v
```

---

## Using Real Project Data

Upload an Excel file with two sheets:

| Sheet | Required columns |
|-------|-----------------|
| `floors` | `floor_id`, `floor_name`, `floor_type`, `slab_area_sqm`, `wall_length_m`, `column_count`, `beam_count` |
| `schedule` | `week`, `wall_panels_demand`, `slab_panels_demand`, `col_panels_demand` |

Sample files are in the `data/` directory.

---

## Academic Grounding

Every algorithm choice is backed by published literature:

| Component | Reference |
|-----------|-----------|
| DBSCAN clustering | Ester et al. (1996), KDD-96 |
| LP BoQ optimization | Hillier & Lieberman (2021), Ch.3 |
| Physical reuse constraint | Hanna (1998), Ch.4; ACI 347R-14 S.5 |
| Design Freeze DI threshold | Ibbs (1997), J. Constr. Eng. Mgmt |
| Outlier detection | Leys et al. (2013), MAD method |
| CBC solver | Forrest & Lougee-Heimer (2005) |

---

## Architecture Principles

- **`backend/` is a strict no-Streamlit zone.** Every module here raises `ValueError` instead of calling `st.error()`. This makes all algorithms independently testable and reusable.
- **`frontend/` only calls backend functions and renders results.** No business logic lives in the UI layer.
- **Charts are in `frontend/charts.py`**, not embedded in page files, so they're independently testable.
- **CSS and color tokens are in `frontend/theme.py`**, not scattered across pages.

---

## Dependencies

```
streamlit
plotly
pulp
scikit-learn
pandas
numpy
scipy
openpyxl
reportlab   # optional — for PDF export
```

---

*FormOptiX — CreaTech '26 · L&T · Problem Statement 4*
