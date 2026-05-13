<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:FF6B00,100:1a1a2e&height=200&section=header&text=FormOptiX&fontSize=72&fontColor=ffffff&fontAlignY=35&desc=Intelligent%20Formwork%20Kitting%20%26%20BoQ%20Optimizer&descAlignY=58&descColor=ffb347&animation=fadeIn" width="100%"/>

<br/>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=FF6B00&center=true&vCenter=true&multiline=true&repeat=true&width=700&height=60&lines=Before+a+single+slab+is+poured.;Algorithmic+formwork+planning+for+L%26T+scale." alt="Typing SVG" />
</p>

<br/>

[![Live Demo](https://img.shields.io/badge/▶%20LIVE%20DEMO-Try%20FormOptiX-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://createchps4teamera-gcrdws5rfnzvfg6vkcrcnn.streamlit.app)
[![R&D Status](https://img.shields.io/badge/Status-Active%20R%26D-blueviolet?style=for-the-badge&logo=flask&logoColor=white)](#rd-log--active-research)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PuLP](https://img.shields.io/badge/PuLP-LP%20Solver-4CAF50?style=for-the-badge&logo=python&logoColor=white)](https://coin-or.github.io/pulp/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-DBSCAN-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![IS 456](https://img.shields.io/badge/IS%20456%3A2000-Strip%20Schedule-blue?style=for-the-badge)](https://bis.gov.in)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![CreaTech](https://img.shields.io/badge/L%26T_CreaTech_'26-Problem_Statement_4-FF6B00?style=for-the-badge)](https://www.larsentoubro.com)

<br/>

> ### 🏆 Finals Submission · L&T CreaTech '26 · Problem Statement 4
> **ERA\_Gati Shakti Vishwavidyalaya**

</div>

---

## 🔬 R&D Log — Active Research

> This repository is under **active R&D** alongside competition preparation.  
> All engineering fixes are logged here with commit references for full traceability.

### Latest R&D Fixes (Post-Submission)

| Fix | Problem | Root Cause | Resolution | Commit |
|-----|---------|-----------|------------|--------|
| **R1** | Column mapping ignored by LP engine | Engine re-read raw file, discarding user's mapping | Cached mapped `df` in `session_state`; engine uses cache instead of re-reading | `f476c23` |
| **R2** | FormOptiX cost > experienced planner (LP couldn't find reuse) | `col_panels` derived from `area/18` ≪ `column_count` demand — LP saw no reuse capacity | `col_panels = column_count`; `wall_panels = wall_length_m/8.5` — matches schedule demand formula exactly | `7e73d4e` |
| **R3** | UnicodeEncodeError crashing Multi-Site & Export tabs | Malformed UTF-16 surrogate pair in lock emoji literal | Replaced broken surrogate with literal `🔒` character | `1f36e4d` |

### Validated Engineering Fixes (Competition Phase)

| Fix | Name | Status | Commit |
|-----|------|--------|--------|
| 1.1 | MAD Override Flag — intentional floor exclusion | ✅ Done | `1ea56a6` |
| 1.2 | DI Consistency — single `df_freeze_active` everywhere | ✅ Done | `6cb6492` |
| 2.1 | LP Fallback Relaxation — two-pass CBC, never crashes | ✅ Done | `b4db6a5` |
| 2.2 | Cross-Site Timestamp Check — 30-min staleness advisory | ✅ Done | `8d6d39a` |
| 2.3 | Freeze/LP Decoupling — guard cached, LP always runs | ✅ Done | `dd3bc2a` |
| 3.0 | IS 456:2000 Stripping — SKU-specific, sidebar toggle | ✅ Done | `443ba27` |

### Open R&D Items

| Item | Description | Priority |
|------|-------------|----------|
| **RD-01** | Bridge dataset cost model — hire rate (₹/m²/day) vs purchase (₹/panel) mismatch | High |
| **RD-02** | Extend schedule weeks to `max(strip_week) + transport` for late-stripping reuse | Medium |
| **RD-03** | Stochastic LP (Phase 2) — Pyomo + Birge & Louveaux (2011) | Roadmap |

---

## 📌 Table of Contents

| # | Section |
|---|---|
| 01 | [The Problem](#-the-problem--why-this-exists) |
| 02 | [The Solution](#-the-solution--what-formoptix-does) |
| 03 | [Impact Numbers](#-impact-numbers) |
| 04 | [Three Core Pillars](#-three-core-pillars) |
| 05 | [Novel Contributions](#-whats-new--novel-contributions) |
| 06 | [System Architecture](#-system-architecture) |
| 07 | [Technical Deep Dive](#-technical-deep-dive) |
| 08 | [Academic Foundation](#-academic-foundation) |
| 09 | [Tech Stack](#-tech-stack) |
| 10 | [Project Structure](#-project-structure) |
| 11 | [Installation & Usage](#-installation--usage) |
| 12 | [Input Format](#-input-format) |
| 13 | [Output](#-output--what-you-get) |
| 14 | [Competitive Landscape](#-competitive-landscape) |
| 15 | [Roadmap](#-roadmap) |
| 16 | [Team](#-team) |
| 17 | [References](#-references) |

---

## 🔴 The Problem — Why This Exists

In a **₹500 Crore construction project**, formwork is the silent cost centre nobody optimises.

```
┌─────────────────────────────────────────────────────────────────┐
│   ₹40 Cr   →  Goes to formwork on a ₹500 Cr project           │
│   ₹12 Cr   →  WASTED — no algorithmic planning                 │
│   3–5 days →  Lost every time drawings change (manual BoQ)     │
│   25–40%   →  Panels sitting idle, tying up capital            │
│   Zero     →  Tools in Primavera, Revit, or SAP that fix this  │
└─────────────────────────────────────────────────────────────────┘
```

**Three root causes:**
1. **No repetition intelligence** — site engineers manually identify similar floors
2. **No LP-based BoQ optimisation** — procurement = demand + 20% buffer
3. **No design freeze protection** — panels ordered while drawings still change *(Ibbs, 1997)*

---

## ✅ The Solution — What FormOptiX Does

FormOptiX is a **Streamlit decision support system** that takes a floor schedule Excel and returns an optimised, procurement-ready Bill of Quantities in under 4 hours — replacing a 5-day manual process.

```
UPLOAD FLOOR SCHEDULE → Data Validation (7 checks) → IS 456:2000 Strip Schedule
→ Design Freeze Guard (cached) → DBSCAN Cluster Floors → Kit Specification
→ Build Reuse Eligibility Matrix → LP BoQ Optimiser (CBC, two-pass fallback)
→ 3-Baseline Savings + Sensitivity → 5-Page PDF + Cross-Site Pool
```

---

## 📊 Impact Numbers

| Metric | Value | Source |
|---|---|---|
| **Formwork cost reduction** | 15.30% | LP vs zero-reuse baseline |
| **BoQ cycle time** | < 4 hours | vs 3–5 days manual |
| **Panel reuse rate** | 60–80% | Peurifoy & Oberlender (2010) |
| **Excess inventory reduction** | ~65% | Idle cost minimisation in LP |
| **Sensitivity range (vs zero)** | 63.5% – 86.1% | 7-scenario LP re-run |
| **Design change probability (DI > 15%)** | 78% | Ibbs (1997) inflection point |

---

## 🏗️ Three Core Pillars

<table>
<tr>
<td width="33%" valign="top">

### 🧠 Pillar 1 — Repetition Intelligence
DBSCAN discovers floor families automatically. IS 456:2000 strip times feed directly into reuse eligibility. Floor override flag lets intentional outliers bypass detection without affecting clustering or the LP.

> **60–80%** reuse benchmark · Peurifoy & Oberlender (2010)

</td>
<td width="33%" valign="top">

### ⚙️ Pillar 2 — LP BoQ Optimiser
Separate LP subproblem per SKU minimises total procurement + holding + idle cost. CBC solver. Two-pass fallback on infeasibility. Savings compared against three baselines.

> **15.30%** savings on demo · **63.5–86.1%** sensitivity range

</td>
<td width="33%" valign="top">

### 🛡️ Pillar 3 — Design Freeze Guard
MAD replaces std (reliable for n < 25). DI computed once at upload and cached. LP always runs regardless of DI status. Predictive probability maps DI to LOW / MODERATE / HIGH.

> **15%** HALT threshold · **78%** late-change probability · Ibbs (1997)

</td>
</tr>
</table>

---

## 🆕 What's New — Novel Contributions

1. **Physical reuse eligibility filter on DBSCAN** — IS 456:2000 strip-time + transport lead time applied before declaring a reuse pair valid
2. **MAD-based procurement gate** — MAD preferred over std for n < 25 *(Leys et al., 2013)*
3. **Three-baseline savings comparison** — Zero reuse + experienced planner (35%) + FormOptiX LP *(Dania et al., 2015)*
4. **Kit Specification panel counts** — exact panel count per SKU from cluster geometry *(Peurifoy & Oberlender, 2010)*
5. **Predictive Design Change Risk** — DI → probability bands + Montgomery upgrade rule
6. **IS 456:2000 as direct LP input** — legally grounded, toggleable to ACI 347R-14
7. **Sensitivity Analysis — OR robustness** — 7-scenario LP re-run *(Hillier & Lieberman, 2021)*
8. **Floor Override Flag** — intentional exceptions excluded from DI everywhere *(Montgomery, 2019 Ch.6)*
9. **LP Two-Pass Fallback** — never crashes or hangs on real data
10. **Cross-Site Freshness Check** — 30-min staleness advisory before reallocation
11. **Column Mapping Cache** *(R1)* — user's column mappings persisted; engine uses cache not raw file
12. **Consistent Reuse Vectors** *(R2)* — `col_panels = column_count`, `wall_panels = wall_length_m/8.5`

---

## 🔬 System Architecture

```
try2_real.py  (Streamlit entry point)
│
├── utils/data_loader.py
│   └── validate_and_map(df, col_map, stripping_standard="IS456")
│       ├── Check A–G: nulls · dupes · schedule logic · positivity · SKU · override
│       ├── get_strip_weeks_is456(df) → IS 456:2000 SKU-based weeks
│       └── get_strip_weeks_aci(df)   → ACI 347R-14 flat week_end+2
│
├── freeze_guard.py  ← computed ONCE, cached in session_state
│   ├── compute_design_freeze(df_freeze_active) → {CV, DI, status}
│   ├── identify_unstable_floors(df) → MAD 2.5× threshold
│   ├── estimate_rework_cost() → 30% penalty (Ibbs 1997)
│   └── compute_change_probability() → LOW/MODERATE/HIGH
│
├── core/clustering.py
│   ├── DBSCAN (eps=0.5, min_samples=2, StandardScaler)
│   ├── build_reuse_matrix() → eligible[i][j]: strip+transport ≤ week_start[j]
│   └── generate_kit_specification() → ceil(avg_area / coverage) + 10% buffer
│
├── core/lp_optimizer.py
│   ├── run_sku_optimizer() — separate LpProblem per SKU (PuLP + CBC)
│   │   ├── Pass 1: C1, C2, C3 standard solve
│   │   └── Pass 2: C3 × 1.20 relaxation if non-Optimal
│   ├── compute_baseline() → zero-reuse cost
│   ├── compute_experienced_planner_baseline() → 35% reuse cost
│   └── compute_sensitivity_analysis() → 7-scenario DataFrame
│
├── utils/report_generator.py
│   └── 5-page PDF: Summary · BoQ · Delivery · Sensitivity · Methodology
│
└── core/cross_site.py
    ├── check_site_data_freshness() → staleness advisory > 30 min
    └── match_supply_to_demand() → greedy first-fit reallocation
```

---

## 🔬 Technical Deep Dive

<details>
<summary><b>🧮 DBSCAN Clustering</b></summary>

Features: `slab_area_m2`, `wall_length_m`, `col_count` — normalised via StandardScaler.
Physical reuse filter: `eligible[i][j] = strip_week[i] + transport ≤ week_start[j]`

IS 456:2000 strip weeks: ALU-600 → 2w · ALU-450 → 1w · H20-beam → 2w

*Sources: Ester et al. (1996), Schubert et al. (2017), IS 456:2000 Cl.11.3*
</details>

<details>
<summary><b>📐 LP Objective Function</b></summary>

```
Minimise: Σ_w ( c_p·x_w + c_h·h_w + c_i·i_w )
C1: x_w + reuse_w + h_(w-1) ≥ D_w
C2: h_w = x_w + reuse_w + h_(w-1) − D_w
C3: x_w ≤ total_demand_sku  (relaxed ×1.20 in Pass 2)
```

Default: c_p = ₹15,000/panel · c_h = ₹500/panel/week · c_i = ₹800/panel/week

*Sources: Hillier & Lieberman (2021), Biruk & Jaskowski (2017)*
</details>

<details>
<summary><b>🛡️ Design Freeze Guard</b></summary>

```
DI = mean(CV_slab, CV_wall, CV_col)
MAD threshold = 2.5 × median(|x_i − median|)   (Leys et al., 2013)
```

| DI | Status | Action |
|---|---|---|
| ≤ 10% | ✅ SAFE | Procure all |
| 10–15% | ⚠️ WARNING | Procure stable only |
| > 15% | 🛑 HALT (advisory) | Freeze drawings |

*Sources: Ibbs (1997), Montgomery (2019), Leys et al. (2013)*
</details>

---

## 📚 Academic Foundation

| Algorithm / Parameter | Source | Used for |
|---|---|---|
| DBSCAN | Ester et al. (1996) | Floor clustering |
| MAD outlier detection | Leys et al. (2013) | Instability detection; 2.5× threshold |
| LP objective | Hillier & Lieberman (2021) Ch.3 | Minimise cost sum |
| LP constraint relaxation | Hillier & Lieberman (2021) Ch.3 | Two-pass fallback |
| 15% DI threshold | Ibbs (1997) | Procurement gate |
| 30% rework penalty | Ibbs (1997) Table 3 | Rework cost estimate |
| IS 456:2000 strip schedule | IS 456:2000 Cl.11.3 | SKU cure times |
| Reuse rate benchmark | Peurifoy & Oberlender (2010) Ch.7 | 60–80% · coverage ratios |
| Experienced planner reuse | Dania et al. (2015) | 35% midpoint |
| Sensitivity analysis | Hillier & Lieberman (2021) Ch.3 | OR validation |
| Operator override | Montgomery (2019) Ch.6 | Floor override flag |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Frontend | Streamlit (7 tabs) |
| ML / Clustering | scikit-learn (DBSCAN, StandardScaler) |
| LP Solver | PuLP + CBC (Coin-or) |
| Data | Pandas + NumPy |
| Visualisations | Plotly |
| PDF Export | ReportLab |
| Input | Excel (.xlsx) via openpyxl |
| Deployment | Streamlit Cloud |

---

## 📁 Project Structure

```
FormOptiX/
├── try2_real.py              ← Streamlit entry point (7 tabs)
├── freeze_guard.py           ← Design Freeze Guard (CV · MAD · predictive)
├── core/
│   ├── clustering.py         ← DBSCAN · reuse matrix · kit specification
│   ├── lp_optimizer.py       ← LP per SKU · two-pass · 3-baseline · sensitivity
│   └── cross_site.py         ← Freshness check · greedy reallocation
├── utils/
│   ├── data_loader.py        ← 7-check validation · IS 456 / ACI toggle
│   ├── demand_calc.py        ← Reuse eligibility matrix
│   └── report_generator.py  ← 5-page PDF (IS 1200 format)
├── data/
│   ├── sample_project.xlsx   ← 10-floor sample
│   └── demo_tower_40floors.xlsx ← 40-floor demo
├── scratch/                  ← 40+ verification scripts
└── requirements.txt
```

---

## ⚙️ Installation & Usage

```bash
git clone https://github.com/ShrutiVerma3008/CreaTech_PS4_TeamERA.git
cd CreaTech_PS4_TeamERA
pip install -r requirements.txt
streamlit run try2_real.py
```

**Live demo:** https://createchps4teamera-gcrdws5rfnzvfg6vkcrcnn.streamlit.app

---

## 📋 Input Format

| Column | Type | Description |
|---|---|---|
| `floor_id` | string | Unique floor identifier |
| `week_start` | int | Construction start week |
| `week_end` | int | Construction end week |
| `strip_week` | int | Strip week (auto-generated if absent) |
| `slab_area_m2` | float | Slab area (m²) |
| `wall_length_m` | float | Wall perimeter (m) |
| `col_count` | int | Column/panel count |
| `panel_type` | string | SKU: `ALU-600`, `ALU-450`, `H20-beam` |
| `floor_override` | bool | Mark intentional exception (optional) |

**Non-standard column names?** FormOptiX shows a dropdown mapping UI automatically — no reformatting needed.

---

## 📤 Output — What You Get

| Tab | Content |
|---|---|
| 🎯 Repetition Analysis | DI gauge · CV table · unstable floors · kit specification |
| 💰 Cost Optimization | 3-baseline savings · BoQ table · sensitivity analysis |
| 📦 Inventory & Forecast | Inventory projections |
| 🏗️ Multi-Site | Freshness check · cross-site reallocation |
| 📄 Export & Reports | 5-page PDF · JSON BoQ |

**PDF pages:** Executive Summary · Full BoQ · Delivery Schedule · Sensitivity Analysis · Methodology + 17 citations

---

## 🆚 Competitive Landscape

| Capability | SAP | Primavera | Doka/PERI | FormOptiX |
|---|---|---|---|---|
| Repetition intelligence | ✗ | ✗ | Partial | ✅ Full |
| Physical reuse filter (IS 456) | ✗ | ✗ | ✗ | ✅ |
| LP BoQ optimisation | ✗ | ✗ | ✗ | ✅ Per SKU/week |
| Design Freeze Guard (MAD) | ✗ | ✗ | ✗ | ✅ |
| 3-baseline savings comparison | ✗ | ✗ | ✗ | ✅ |
| Sensitivity analysis (7 scenarios) | ✗ | ✗ | ✗ | ✅ |
| Cross-site freshness check | ✗ | ✗ | ✗ | ✅ |
| Column mapping UI | ✗ | ✗ | ✗ | ✅ |
| 17 peer-reviewed citations | ✗ | ✗ | ✗ | ✅ |

---

## 🗺️ Roadmap

```
Phase 1 — NOW ✅      Phase 2 — 9–18 months     Phase 3 — 18–36 months
────────────────      ─────────────────────      ─────────────────────
Excel input           BIM API connector           SAP/Oracle ERP sync
IS 456:2000           FastAPI + Celery async PDF  AI auto-procurement
3-pillar engine       Stochastic LP               National yard network
Sensitivity (7 LP)    RFID digital twin           SaaS for industry
5-page PDF            10+ sites live
Cross-site pool
Column mapping (R1)
Reuse vector fix (R2)
```

---

## 👥 Team

| | **Aryan Thakur** | **Shruti Verma** | **Srijan Gupta** |
|---|---|---|---|
| Role | Backend & LP Engine | Frontend & Deployment | ML & Clustering |
| Focus | PuLP · IS 456 · sensitivity · two-pass fallback | Streamlit · PDF · Export tab | DBSCAN · MAD · kit specification |

**Institution:** ERA\_Gati Shakti Vishwavidyalaya · **Competition:** L&T CreaTech '26 · PS4 · Finals

---

## 📚 References

| # | Reference | Used for |
|---|---|---|
| [1] | Ester et al. (1996). KDD-96. | DBSCAN |
| [2] | Schubert et al. (2017). ACM TODS 42(3). | DBSCAN parameters |
| [3] | Leys et al. (2013). J. Exp. Social Psych. 49(4). | MAD; 2.5× threshold |
| [4] | Hillier & Lieberman (2021). OR 11th ed. Ch.3. | LP objective · relaxation · sensitivity |
| [5] | Biruk & Jaskowski (2017). Archives of Civil Eng. | LP for construction |
| [6] | Mitchell et al. (2011). PuLP. Univ. Auckland. | Solver implementation |
| [7] | Forrest & Lougee-Heimer (2005). INFORMS. | CBC solver |
| [8] | Ibbs (1997). J. Const. Eng. Mgmt. 123(3). | 15% DI · 30% rework · probability |
| [9] | Montgomery (2019). SQC 8th ed. Ch.6. | CV stability · operator override |
| [10] | ACI 347R-14 S.5. ACI (2014). | Strip time (international) |
| [11] | IS 456:2000 Cl.11.3. BIS. | Strip time (Indian standard) |
| [12] | Hanna (1998). Concrete Formwork. Ch.4. | Panel cycling |
| [13] | Peurifoy & Oberlender (2010). Formwork 4th ed. Ch.7. | Reuse benchmark · coverage ratios |
| [14] | IS 1200 Part 1 (1992). BIS. | BoQ column format |
| [15] | PMI PMBOK 7th ed. S.4.3 (2021). | BoQ as procurement document |
| [16] | Dania et al. (2015). J. Eng. Design Tech. 13(3). | Cross-site reallocation · 35% reuse |
| [17] | Birge & Louveaux (2011). Stochastic Programming. Springer. | Phase 2: stochastic LP |

---

## 🔢 Key Numbers

| Parameter | Value | Source |
|---|---|---|
| DI HALT threshold | > 15% | Ibbs (1997) |
| Rework penalty | 30% | Ibbs (1997) Table 3 |
| MAD multiplier | 2.5× | Leys et al. (2013) |
| Experienced planner reuse | 35% | Dania et al. (2015) |
| ALU-600 strip weeks | 2 w | IS 456:2000 Cl.11.3 |
| ALU-450 strip weeks | 1 w | IS 456:2000 Cl.11.3 |
| LP C3 relaxation | ×1.20 | Hillier & Lieberman (2021) |
| Freshness threshold | 30 min | Dania et al. (2015) |
| Kit buffer | 10% | Peurifoy & Oberlender (2010) |
| Sensitivity range | 63.5%–86.1% | 7-scenario LP |
| Academic citations | 17 | Every threshold cited |
| Verification tests | 40+ | All gap + fix scripts |
| R&D commits | `f476c23` `7e73d4e` `1f36e4d` | R1 · R2 · R3 |
| Fix commits | `1ea56a6` `6cb6492` `b4db6a5` `8d6d39a` `dd3bc2a` `443ba27` | Fixes 1.1–3.0 |

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a1a2e,100:FF6B00&height=120&section=footer&text=FormOptiX&fontSize=32&fontColor=ffffff&fontAlignY=65&animation=fadeIn" width="100%"/>

**Built with ❤️ by ERA\_Gati Shakti Vishwavidyalaya**
**for L&T CreaTech '26 · Problem Statement 4**

*"Before a single slab is poured."*

[![Live Demo](https://img.shields.io/badge/▶%20Try%20It%20Now-FormOptiX%20Live-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://createchps4teamera-gcrdws5rfnzvfg6vkcrcnn.streamlit.app)

</div>
