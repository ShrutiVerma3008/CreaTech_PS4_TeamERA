# FormOptiX — The Developer's Guide 💻

*Hey there! If you're looking for the business case or a high-level overview, check out the main [README.md](README.md).*

Welcome to the technical docs for FormOptiX. If you're a Data Scientist, Software Engineer, or a Hackathon Judge diving into our codebase, you're in the right place. We wrote this to help you understand how our engine works, how we built the architecture, and how you can actually extend this code if you want to.

---

## 🏗️ How We Built It (Clean Architecture)

We didn't just write a massive, messy script. FormOptiX uses a strict **Separation of Concerns** (Clean Architecture) pattern. We purposefully kept the heavy math completely separate from the UI.

### The Golden Rule: The Backend is a Streamlit-Free Zone

If you look inside the `backend/` folder, you'll notice a few strict rules we followed:
1. **No `import streamlit` — ever.** If we tied the math to the UI, you couldn't easily plug this into an ERP system later.
2. **Standard exceptions only.** Our functions raise standard `ValueError`s with helpful messages instead of using `st.error()`. The frontend handles catching and showing them.
3. **Pure data in, pure data out.** Everything runs on plain Pandas DataFrames, lists, or dicts. No weird side effects.

Because we built it this way, you could theoretically:
- Wrap the backend in FastAPI and deploy it as a REST endpoint in half an hour.
- Plug it straight into SAP or a custom ERP without rewriting the algorithms.
- Run the whole engine inside a Jupyter Notebook for research.

### How Data Flows Through the App

```
User Input (Sidebar/Upload)
        │
        ▼
frontend/app.py  ──────────────────────────────────────────┐
   │  (The boss: reads inputs, calls backend, saves          │
   │   results in st.session_state, and handles routing)     │
   │                                                         │
   ├──► backend/utils/synthetic_data.py  (demo mode)         │
   │    └──► generates fake (df_floors, df_schedule)         │
   │                                                         │
   ├──► backend/utils/data_loader.py  (real mode)            │
   │    └──► validate_and_map() ─► raises a ValueError if    │
   │                                the Excel file is messy  │
   │                                                         │
   ├──► backend/core/freeze_guard.py                         │
   │    └──► compute_design_freeze(df_floors) ─► returns DI  │
   │                                                         │
   ├──► backend/core/clustering.py                           │
   │    └──► compute_repetition_score() ─► returns clusters, │
   │         scores, and reuse pairs                         │
   │    └──► generate_kit_bom(cluster_summary) ─► BOM dict   │
   │                                                         │
   ├──► backend/core/lp_optimizer.py                         │
   │    └──► run_sku_optimizer() ─► returns LP results,      │
   │         savings, and chart data                         │
   │                                                         │
   └──► frontend/pages/*.py  (takes the data and draws it)   │
         └──► frontend/charts.py  (builds the go.Figure)     │
                                                             │
        st.session_state (our shared memory) ───────────────┘
```

---

## 📁 A Quick Tour of the Folders

```text
FormOptiX/
│
├── backend/                        # All the math and logic. Zero UI code.
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py             # Easy exports for the main functions
│   │   ├── clustering.py           # DBSCAN + physical reuse rules + Kit BOM generator
│   │   ├── lp_optimizer.py         # The PuLP ILP solver (3 SKUs, 52 weeks)
│   │   ├── freeze_guard.py         # The Design Instability (DI) index math
│   │   └── cross_site.py           # The greedy algorithm for matching idle panels
│   └── utils/
│       ├── __init__.py             # Loads reportlab lazily so it doesn't break if missing
│       ├── data_loader.py          # Validates and cleans up messy Excel uploads
│       ├── demand_calc.py          # Figures out which panels can actually be reused
│       ├── synthetic_data.py       # Builds our fake demo building and forecasts demand
│       └── report_generator.py     # Spits out the PDF BoQ report
│
├── frontend/                       # All the pretty UI stuff
│   ├── app.py                      # Main entry point, sidebar, and tab routing
│   ├── theme.py                    # All our colors, CSS, and Plotly styling in one place
│   ├── charts.py                   # Every chart builder function (easy to test on their own)
│   └── pages/
│       ├── __init__.py
│       ├── repetition.py           # Tab 1: Gauges, clusters, Kit BOM, and DFI
│       ├── cost.py                 # Tab 2: ROI numbers, LP tables, waterfall charts
│       ├── inventory.py            # Tab 3: Inventory curves and forecasting
│       ├── building_data.py        # Tab 4: Raw data tables and scatter plots
│       ├── roadmap.py              # Tab 5: Our future plans and competitive matrix
│       └── portfolio.py            # Tab 6: The cross-site reallocation demo
│
├── tests/                          # 30 automated tests to keep us sane
│   ├── __init__.py
│   ├── test_clustering.py          
│   ├── test_cross_site.py
│   ├── test_data_loader.py
│   ├── test_freeze_guard.py
│   └── test_synthetic_data.py
│
├── data/                           # Some sample Excel files you can play with
│   ├── demo_tower_40floors.xlsx
│   ├── formoptix_real_project.xlsx
│   └── sample_project.xlsx
│
├── docs/assets/
├── requirements.txt
├── README.md                       # The business pitch
└── README_for_nerds.md             # You are here!
```

---

## ⚙️ How the Math Actually Works

### 1. Repetition Clustering (`backend/core/clustering.py`)

**Why did we use DBSCAN instead of K-Means?**

K-Means is great, but it forces *every* data point into a cluster, and you have to guess how many clusters there are beforehand. In a real 40-floor building, you usually have a few weird podium floors, a couple of mechanical floors, and maybe a penthouse. 

DBSCAN handles this perfectly. It finds the dense group of "typical" floors and labels all the weird, unique floors as noise (`cluster = -1`). That way, our Repetition Score and Kit BOM are based purely on the standard floors and don't get skewed by the shape of the lobby.

**The Filter That Matters (Physical Reuse):**
Just because two floors are the same shape doesn't mean you can share panels between them. We apply a second filter based on actual construction physics:

```python
# A panel from floor A can only be reused on floor B if:
strip_week[A] + transport_weeks <= week_start[B]
```
This rule is straight out of the ACI 347R-14 guidelines for concrete curing times. If a cluster of floors doesn't have enough time between them to actually move the panels, we toss the cluster out. We don't want the optimizer relying on physically impossible reuse.

---

### 2. Kit BOM Generator (`generate_kit_bom()`)

Once we find that dominant cluster, we need to know exactly what panels to order for it. We take the average geometry and convert it into a standard industry Bill of Materials (assuming standard aluminum formwork):

```python
wall_panels_600mm       = int(avg_wall_length  / 0.6)
slab_panels_1500x1000   = int(avg_slab_area    / 1.5)
col_panels_standard     = int(avg_column_count * 4)
```

---

### 3. The LP BoQ Optimizer (`backend/core/lp_optimizer.py`)

We treat procurement as an **Integer Linear Programming (ILP)** problem and solve it using the `PuLP` library (specifically with the CBC solver). We run three independent subproblems (one for walls, slabs, and columns).

**What we are trying to minimize:**
We want the lowest possible combined cost of:
`(Cost to Buy × Panels Bought) + (Rental Cost × Panels Held) + (Penalty Cost × Idle Panels)`

**The Rules (Constraints):**
1. **Demand Rule:** Inventory must always be enough to meet that week's demand.
2. **Balance Rule:** This week's inventory is simply whatever you bought + whatever you reused + whatever you held over from last week, minus what you actually used.
3. **Purchase Cap:** You can't just buy infinite panels to solve the problem.

*Note: If someone tries to run this without PuLP installed, we gracefully fall back to a Just-In-Time (JIT) heuristic so the app doesn't crash.*

---

### 4. Design Freeze Intelligence (`backend/core/freeze_guard.py`)

We calculate a **Design Instability (DI)** index by looking at the Coefficient of Variation (CV) across recent design revisions. 

If `DI > 15%`, we throw a `HALT` warning. Why 15%? Studies (like Ibbs, 1997) show that when design variation crosses this threshold, rework rates skyrocket. 

We also use the **MAD (Median Absolute Deviation)** method to pinpoint exactly *which* floors are causing the instability, since it handles outliers better than standard deviation.

---

### 5. Cross-Site Reallocation (`backend/core/cross_site.py`)

To match idle panels at Site A to needs at Site B, we use a **Greedy First-Fit Algorithm**. It simply checks the demand, looks for available idle panels at other sites that can be shipped in time, makes the match, and deducts from the idle pool. 

Is it mathematically optimal across the whole network? No, a full multi-site ILP would be better, but for a prototype, this O(n×m) approach is fast, effective, and much easier to explain to site engineers.

---

## 🛠️ Want to Hack on This?

### How to add a new Clustering Algorithm
Think you have a better way to group floors?
1. Create `backend/core/your_awesome_algorithm.py`.
2. Make sure your main function accepts a DataFrame and returns the same tuple signature as `compute_repetition_score`.
3. Pop into `frontend/app.py` and swap out the import to point to your new function. Done!

### How to add a new UI Tab
1. Create a new file like `frontend/pages/my_cool_tab.py`.
2. Give it a `render(state: dict)` function. The `state` dictionary holds all the app data you need.
3. Open `frontend/app.py`, import your tab, add its name to the `st.tabs()` list, and call `pg_my_cool_tab.render(shared)` inside the tab block.

### How to add a new Chart
1. Build the Plotly figure in `frontend/charts.py`. (Remember: return the `go.Figure`, don't use `st.plotly_chart` in here!)
2. Import that builder function into whatever page you want to show it on, and render it there.

---

## 🧪 Testing (Because we like code that works)

We wrote **30 automated tests** to make sure we don't break things while hacking. They test everything from Excel validation to the cross-site logic.

To run them, just pop open your terminal and type:
```bash
python3 -m pytest tests/ -v
```

**Testing Philosophy:**
- Because the backend is pure Python, we don't need messy Streamlit mocks. We just import the functions and pass them fake DataFrames.
- We use `@pytest.fixture` to whip up tiny, 10-row DataFrames that quickly test boundary conditions (like what happens if there are zero idle panels?).
- We use `np.random.seed(0)` so our tests behave the same way every single time.

---

## 📦 What We're Using (Dependencies)

Here's the stack we rely on:

| Package | What it does |
|---------|-------------|
| `streamlit` | Makes the UI look great without writing HTML/JS |
| `plotly` | Builds those interactive charts |
| `pandas` & `numpy` | Heavy lifting for all the data manipulation |
| `scikit-learn` | Powers the DBSCAN clustering |
| `scipy` | Handles the stats math (like MAD and CV) |
| `pulp` | Solves the ILP optimization math |
| `openpyxl` | Lets us read those Excel uploads |
| `reportlab` | *(Optional)* Used to generate the PDF BoQ export |

Install the core stuff with:
```bash
pip install -r requirements.txt
```

---

## 📚 Where We Got Our Math (References)

We didn't just make this up. Here's the academic backing for the engine:

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
