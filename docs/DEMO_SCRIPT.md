# FormOptiX — 3-Minute Finals Demo Script

## Setup (before judges arrive)
- Open try2_real.py in browser (streamlit run try2_real.py)
- Load data/demo_tower_40floors.xlsx in Real Site Data mode
- Set sidebar: transport_weeks=1, strip_buffer=2
- Set cost params: c_p=15000, c_h=500, c_i=800
- Click Run FormOptiX Engine once to pre-load results
- Have Tab 1, Tab 2, and Tab 6 open in browser

---

## Minute 1 — The Problem (0:00–1:00)

SAY: "In a Rs 500 Cr construction project, 8% goes to
formwork — roughly Rs 40 Cr. Without algorithmic planning,
25-40% of panels sit idle. That is Rs 10-16 Cr of idle
capital on a single project."

SHOW: The uploaded floor schedule (40 floors, 3 panel types)

SAY: "FormOptiX takes this schedule and does three things
automatically."

---

## Minute 2 — The Three Pillars (1:00–2:00)

### Pillar 1 — Design Freeze Guard (Tab 1, top section)
SHOW: DI gauge chart

SAY: "Before we order a single panel, we check if the
drawings are stable enough to procure. Our Design
Instability Index is based on Ibbs (1997) — projects
above 15% DI show 3x higher rework costs."

POINT TO: The gauge needle and the green/yellow/red zones.

SAY: "For this project the DI is [read value]% — that
means [SAFE: proceed / WARNING: partial / HALT: wait]."

### Pillar 2 — Floor Clustering (Tab 1, middle section)
SHOW: The cluster output and reuse pair table

SAY: "DBSCAN groups geometrically similar floors into
reuse families. Floors 1-12 form Cluster A — same panel
kit, reused across all 12 floors. The reuse coefficient
here is [read rho_k value]%, against an industry
benchmark of 60-80% from Peurifoy & Oberlender (2010)."

### Pillar 3 — LP BoQ Optimizer (Tab 2)
SHOW: The 4-column savings metrics

SAY: "The LP minimizes procurement plus holding plus
idle cost per SKU per week. On this 40-floor project,
optimized cost is Rs [X] Cr versus a baseline of Rs [Y]
Cr — a saving of Rs [Z] Cr, or [%]%."

SHOW: Move the what-if slider to 15%

SAY: "If design changes by 15% mid-project, that saving
drops to Rs [new value] Cr. The tool shows you the cost
of design instability in rupees, before it happens."

---

## Minute 3 — Output & Scale (2:00–3:00)

### PDF Export
SHOW: Click Export BoQ as PDF, open the downloaded PDF

SAY: "The output is not a chart — it is a signable
procurement document in IS 1200 format that a vendor
can act on today."

### Cross-Site (Tab 6) — if judges ask about scale
SHOW: Tab 6

SAY: "L&T runs 50+ concurrent sites. This tab lets site
managers upload BoQ files from multiple projects and
identifies idle panels that can be reallocated instead
of procured fresh. Even a 10% cross-site reallocation
rate on Rs 40 Cr of formwork saves Rs 4 Cr per project."

---

## Anticipated judge questions

Q: "Is the 15% DI threshold arbitrary?"
A: "No. It is calibrated from Ibbs (1997) which studied
60 construction projects and found the rework cost curve
inflects sharply at 15% scope variance."

Q: "Why DBSCAN and not k-means?"
A: "K-means requires specifying the number of clusters
in advance. We do not know how many typical floor types
a building has before analyzing it. DBSCAN discovers
clusters automatically and marks atypical floors as noise,
which is exactly what we need — per Ester et al. (1996)."

Q: "What is your validation dataset?"
A: "We validated on a synthetic 40-floor tower matching
typical L&T residential high-rise specifications. The LP
produces the mathematical optimum for given inputs —
deviation from manual BoQ equals manual planning overhead,
not algorithmic error."

Q: "Can this work with BIM data?"
A: "Currently we use Excel input — no BIM dependency,
which means any site engineer can use it today without
licensing costs. BIM API integration is Phase 2 of our
roadmap."

Q: "Why not use Gurobi or CPLEX?"
A: "PuLP with CBC solver is academically validated
(Forrest & Lougee-Heimer, 2005) and license-free.
For production scale with 100+ sites, commercial
solvers are a straightforward drop-in upgrade."

---

## Numbers to memorize before presenting
- DI threshold: 15% (Ibbs, 1997)
- Reuse benchmark: 60-80% (Peurifoy & Oberlender, 2010)
- Rework penalty factor: 30% (Ibbs, 1997, Table 3)
- MAD threshold: 2.5× (Leys et al., 2013)
- DBSCAN paper: Ester et al. (1996), KDD-96
- LP reference: Hillier & Lieberman (2021), Ch.3

---

*FormOptiX — L&T CreaTech '26, Problem Statement 4*
*ERA_Gati Shakti Vishwavidyalaya*
