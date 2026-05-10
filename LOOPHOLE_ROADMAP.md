# FormOptiX — Loophole Roadmap Defense
## L&T CreaTech '26 Finals · Problem Statement 4

> This document is the **complete technical defense record** for every
> potential judge challenge against FormOptiX. Each "loophole" is a
> specific weakness a judge could identify; each "fix" is the
> implemented resolution with academic backing and a passing test suite.

---

## Status Overview

| Fix | Name | Commit | Tests |
|-----|------|--------|-------|
| 1.1 | MAD Override Flag | `1ea56a6` | 7/7 ✅ |
| 1.2 | DI Consistency (df_freeze_active) | `6cb6492` | 7/7 ✅ |
| 2.1 | LP Fallback Relaxation | `b4db6a5` | 5/5 ✅ |
| 2.2 | Cross-Site Timestamp Check | `8d6d39a` | 6/6 ✅ |
| 2.3 | Freeze Guard / LP Decoupling | `dd3bc2a` | 6/6 ✅ |

**All 5 fixes implemented, committed, pushed. All test suites pass (exit 0).**

---

## Fix 1.1 — MAD Override Flag

### Judge Challenge
> *"Your system flags F36 as unstable. But F36 is a mechanical floor —
> intentionally different. Your outlier detector has no way to know that.
> You're crying wolf."*

### Root Cause
`identify_unstable_floors()` in `freeze_guard.py` ran 2.5× MAD detection
on **all** floors, including ones that are architecturally intentional
deviations (refuge floors, mechanical floors, lobbies).

### Fix
Added a `floor_override` boolean column to the data schema.
`identify_unstable_floors()` pre-filters to `df_active` (rows where
`floor_override == False`) before any MAD loop.

### Academic Backing
- **Leys et al. (2013)** J.Exp.Social Psych. 49(4) 764–766 → MAD is
  robust to outliers but cannot distinguish intentional from
  unintentional deviation — human override is the correct resolution.
- **Montgomery (2019)** Statistical Quality Control 8th ed. Ch.6 →
  process control charts always allow operator override for known
  special causes.

### Demo Behaviour
`demo_tower_40floors.xlsx` has `floor_override = True` for F36–F40.
These floors are excluded from the MAD scan and listed in an
`st.info()` banner in Tab 1.

### Verification
```
python scratch/verify_fix1_1.py   # 7/7 pass, exit 0
```

---

## Fix 1.2 — DI Consistency

### Judge Challenge
> *"You say F36–F40 are excluded from instability detection. But your
> DI gauge still reads 31.3% which includes their data. The gauge and
> the table are inconsistent."*

### Root Cause
`compute_design_freeze()` was called with the full `df_floors` (all 40
floors), while `identify_unstable_floors()` used `df_active` (35 floors).
Two different datasets → two different stories.

### Fix
Built `df_freeze_active` (same override filter) **before** calling
`compute_design_freeze`. Stored it to `session_state["df_freeze_active"]`
so `compute_change_probability` uses the same subset. All DI numbers
shown anywhere in the app now come from the same 35-floor dataset.

### Result
DI drops from **31.29% → 20.80%** when F36–F40 are excluded.
The status banner appends `"(5 intentional floor(s) excluded — Montgomery 2019 Ch.6)"`.

### Verification
```
python scratch/verify_fix1_1.py   # Test 7 specifically tests DI drop
```

---

## Fix 2.1 — LP Fallback Relaxation

### Judge Challenge
> *"What happens if your LP solver fails on a real client's data?
> Will the app crash with a Python traceback in front of the panel?"*

### Root Cause
`_run_sku_lp()` returned a raw error dict on non-Optimal status, and
`run_sku_optimizer()` did an early-return on the first failed SKU,
abandoning all remaining SKUs. No fallback existed.

### Fix
**Two-pass fallback** inside `_run_sku_lp()`:

| Pass | C3 cap | On success |
|------|--------|------------|
| 1 | `total_demand_sku` | rows with `"relaxed": False` |
| 2 | `total_demand_sku × 1.20` | rows with `"relaxed": True` |
| Both fail | — | clean `{"status":"infeasible"}` dict — never raises |

`run_sku_optimizer()` continues past a failed SKU instead of stopping.
Tab 2 shows a `st.warning()` (relaxed) or `st.error()` (infeasible) banner.

### Academic Backing
- **Hillier & Lieberman (2021)** Ch.3 → constraint relaxation is
  standard LP recovery methodology.
- **Forrest & Lougee-Heimer (2005)** INFORMS → CBC non-Optimal status
  must be handled explicitly; solver does not raise exceptions.
- **Mitchell et al. (2011)** PuLP Toolkit → always check
  `LpStatus[prob.status]`, never assume optimal.

### Verification
```
python scratch/verify_fix2_1.py   # 5/5 pass, exit 0
```

---

## Fix 2.2 — Cross-Site Timestamp Check

### Judge Challenge
> *"Site A and Site B data are uploaded independently. How do you know
> they're from the same project version? If I upload a stale Site B
> file, your cross-site matching is comparing apples and oranges."*

### Root Cause
Tab 6 ran `match_supply_to_demand(idle, demand)` with no awareness of
when each site's data was loaded. Stale data → silent mis-match.

### Fix
New function `check_site_data_freshness(ts_a, ts_b, threshold_minutes=30)`
in `core/cross_site.py`. Captures `datetime.datetime.now()` into
`session_state` immediately after each site file upload. Before
`match_supply_to_demand()` is called, computes `|ts_a − ts_b|` in
minutes and shows:
- **`st.warning()`** (yellow) if gap > 30 min — with exact ISO timestamps
- **`st.success()`** (green) if within threshold

Handles `None` timestamps gracefully — never crashes.

### Academic Backing
- **Dania et al. (2015)** J.Eng.Design Tech. 13(3) 376–399 →
  cross-site reallocation is only valid when site data is
  temporally consistent.
- **PMI PMBOK 7th ed. S.4.3 (2021)** → procurement decisions
  require version-controlled inputs; stale data invalidates
  cross-site allocation.

### Verification
```
python scratch/verify_fix2_2.py   # 6/6 pass, exit 0
```

---

## Fix 2.3 — Freeze Guard / LP Decoupling

### Judge Challenge
> *"If the freeze guard fires mid-LP-run and re-computes DI, it could
> conflict with the optimizer. How do you prevent that? And what if
> the user jumps straight to Tab 2 — does `freeze_result` even exist?"*

### Root Cause
1. `compute_design_freeze()` was called on every `run_btn` press with
   no cache, meaning repeated runs could re-enter the guard while
   the LP was using the previous result.
2. `freeze_result` was only set during `run_btn`, so navigating to
   Tab 2 in a fresh session (before any Run) raised `KeyError` risk.
3. A HALT status in the run block had historically included a hard
   `st.stop()` comment (now removed); Tab 2 had no advisory at all.

### Fix
Three-part change (all in `try2_real.py` only):

**Part A — `freeze_source_file` guard** (`run_btn` block):
```python
_freeze_needs_recompute = (
    "freeze_result" not in st.session_state
    or st.session_state.get("freeze_source_file") != _freeze_file_key
)
if _freeze_needs_recompute:
    freeze_result = compute_design_freeze(df_freeze_active)
    st.session_state["freeze_source_file"] = _freeze_file_key
else:
    freeze_result = st.session_state.freeze_result   # use cache
```
DI is computed **once per file upload**, not on every Run press.

**Part B — Tab 2 soft advisory** (no `st.stop()`):
```
HALT    → st.warning()  "Results indicative only — engineer retains authority"
WARNING → st.info()     "Consider procuring stable clusters only"
SAFE    → silence       LP runs normally
```
LP always runs regardless of freeze status.

**Part C — Tab 1 safe fallback**:
```python
if freeze_result is None:
    st.info("Upload a project file to see Design Freeze Analysis.")
```
No `KeyError` possible.

### Academic Backing
- **Ibbs (1997)** J.Const.Eng.Mgmt. 123(3) 308–311 → freeze guard
  is an advisory signal, not a hard procurement block; procurement
  decisions remain with the engineer.
- **Hillier & Lieberman (2021)** Ch.3 → LP constraints and external
  guards must be decoupled to guarantee convergence.
- **Montgomery (2019)** Statistical Quality Control 8th ed. Ch.6 →
  control chart signals are advisory; operator retains authority.

### Verification
```
python scratch/verify_fix2_3.py   # 6/6 pass, exit 0
```

---

## Full Regression — All Suites Green

```
verify_fix1_1.py       7/7  ✅  (Fix 1.1 + Fix 1.2)
verify_fix2_1.py       5/5  ✅  (Fix 2.1)
verify_fix2_2.py       6/6  ✅  (Fix 2.2)
verify_fix2_3.py       6/6  ✅  (Fix 2.3)
verify_gap2.py         ✅   (Three-baseline savings)
verify_gap3.py         ✅   (Design Change Probability)
verify_gap4.py         ✅   (Sensitivity Analysis)
verify_sensitivity.py  ✅   (Sensitivity table display)
verify_kit_spec.py     ✅   (Gap 1 Kit Specification)
verify_export_tab.py   ✅   (PDF + JSON export, Tab 7)
```

---

## Academic Reference Index

| Citation | Used In |
|----------|---------|
| Leys et al. (2013). J.Exp.Social Psych. 49(4) | Fix 1.1, Fix 1.2 |
| Montgomery (2019). SQC 8th ed. Ch.6 | Fix 1.1, Fix 1.2, Fix 2.3 |
| Hillier & Lieberman (2021). OR 11th ed. Ch.3 | Fix 2.1, Fix 2.3 |
| Forrest & Lougee-Heimer (2005). INFORMS CBC | Fix 2.1 |
| Mitchell et al. (2011). PuLP Toolkit | Fix 2.1 |
| Dania et al. (2015). J.Eng.Design Tech. 13(3) | Fix 2.2, Gap 1–4 |
| PMI PMBOK 7th ed. S.4.3 (2021) | Fix 2.2 |
| Ibbs (1997). J.Const.Eng.Mgmt. 123(3) | Fix 2.3, Gap 3 |
