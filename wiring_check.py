# -*- coding: utf-8 -*-
"""
wiring_check.py — FormOptiX wiring verification
================================================
Read-only: does NOT modify any file.
Checks try2_real.py (and freeze_guard.py) for correct wiring.
Run: python wiring_check.py
"""
import sys, pathlib, re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT   = pathlib.Path(__file__).parent
MAIN   = ROOT / "try2_real.py"
FG     = ROOT / "freeze_guard.py"

PASS = "[PASS]"
FAIL = "[FAIL]"
SEP  = "=" * 62

results = {}

def read_lines(path):
    return path.read_text(encoding="utf-8").splitlines()

main_lines = read_lines(MAIN)

def find_lines(lines, pattern, is_regex=False):
    """Return list of (1-based line number, stripped content) matching pattern."""
    hits = []
    for i, ln in enumerate(lines, 1):
        if is_regex:
            if re.search(pattern, ln):
                hits.append((i, ln.strip()))
        else:
            if pattern in ln:
                hits.append((i, ln.strip()))
    return hits


# ──────────────────────────────────────────────────────────────
# CHECK 1 — freeze_guard import present in try2_real.py
# ──────────────────────────────────────────────────────────────
print("\n" + SEP)
print("CHECK 1 — freeze_guard import in try2_real.py")
print(SEP)

hits_fg_import = (
    find_lines(main_lines, "from freeze_guard import compute_design_freeze") +
    find_lines(main_lines, "from core.freeze_guard import compute_design_freeze")
)

if hits_fg_import:
    for ln, txt in hits_fg_import:
        print(f"  FOUND  line {ln:5d}: {txt}")
    print(f"\n{PASS} freeze_guard import present.")
    results["import"] = (True, hits_fg_import)
else:
    print("  NOT FOUND in try2_real.py")
    print(f"\n{FAIL} freeze_guard import is MISSING.")
    results["import"] = (False, [])


# ──────────────────────────────────────────────────────────────
# CHECK 2 — compute_design_freeze() called BEFORE clustering call
# ──────────────────────────────────────────────────────────────
print("\n" + SEP)
print("CHECK 2 — compute_design_freeze() call before clustering")
print(SEP)

freeze_calls   = find_lines(main_lines, "compute_design_freeze(", is_regex=False)
cluster_calls  = find_lines(main_lines, "compute_repetition_score(", is_regex=False)

print("  compute_design_freeze() occurrences:")
for ln, txt in freeze_calls:
    print(f"    line {ln:5d}: {txt}")

print("  compute_repetition_score() occurrences:")
for ln, txt in cluster_calls:
    print(f"    line {ln:5d}: {txt}")

# Exclude occurrences inside function *definitions* (def lines)
freeze_call_lines  = [ln for ln, txt in freeze_calls  if not txt.startswith("def ")]
cluster_call_lines = [ln for ln, txt in cluster_calls if not txt.startswith("def ")]

if not freeze_call_lines:
    print(f"\n{FAIL} compute_design_freeze() is NEVER called in try2_real.py.")
    results["call_order"] = (False, "freeze call missing")
elif not cluster_call_lines:
    print(f"\n{FAIL} compute_repetition_score() is NEVER called in try2_real.py.")
    results["call_order"] = (False, "clustering call missing")
else:
    first_freeze  = min(freeze_call_lines)
    first_cluster = min(cluster_call_lines)
    if first_freeze < first_cluster:
        print(f"\n{PASS} Freeze check (line {first_freeze}) is BEFORE "
              f"clustering (line {first_cluster}).")
        results["call_order"] = (True, f"freeze={first_freeze}, cluster={first_cluster}")
    else:
        print(f"\n{FAIL} Freeze check (line {first_freeze}) is AFTER or SAME AS "
              f"clustering (line {first_cluster}). ORDER IS WRONG.")
        results["call_order"] = (False, f"freeze={first_freeze}, cluster={first_cluster}")


# ──────────────────────────────────────────────────────────────
# CHECK 3 — LP solver status guard in try2_real.py
# ──────────────────────────────────────────────────────────────
print("\n" + SEP)
print("CHECK 3 — LP solver status guard (st.error + st.stop on non-Optimal)")
print(SEP)

# Look for the guard pattern: status check that leads to st.stop()
guard_hits = find_lines(main_lines,
    r'lp_status\s*not\s*in|status\s*!=\s*["\']Optimal', is_regex=True)
stop_hits  = find_lines(main_lines, "st.stop()", is_regex=False)
error_hits = find_lines(main_lines, r'st\.error.*lp_status|st\.error.*Optimal|st\.error.*Solver',
                        is_regex=True)

print("  Status guard condition lines:")
for ln, txt in guard_hits:
    print(f"    line {ln:5d}: {txt}")
print("  st.stop() occurrences:")
for ln, txt in stop_hits:
    print(f"    line {ln:5d}: {txt}")
print("  LP-related st.error() lines:")
for ln, txt in error_hits:
    print(f"    line {ln:5d}: {txt}")

if guard_hits and stop_hits:
    # Verify a st.stop() follows a guard line within 10 lines
    guard_lnums = [ln for ln, _ in guard_hits]
    stop_lnums  = [ln for ln, _ in stop_hits]
    close_stop  = any(
        any(abs(s - g) <= 10 for s in stop_lnums)
        for g in guard_lnums
    )
    if close_stop:
        print(f"\n{PASS} LP status guard found with st.stop() nearby.")
        results["lp_guard"] = (True, f"guard={guard_lnums}, stops={stop_lnums}")
    else:
        print(f"\n{FAIL} Status guard found but st.stop() is NOT within 10 lines.")
        results["lp_guard"] = (False, "stop() too far from guard")
else:
    missing = []
    if not guard_hits: missing.append("status guard condition")
    if not stop_hits:  missing.append("st.stop()")
    print(f"\n{FAIL} Missing: {', '.join(missing)}")
    results["lp_guard"] = (False, f"missing {missing}")


# ──────────────────────────────────────────────────────────────
# CHECK 4 — lp_optimizer section: weekly cap removed, demand-derived caps present
# ──────────────────────────────────────────────────────────────
print("\n" + SEP)
print("CHECK 4 — LP: weekly budget cap removed, demand-derived caps in place")
print(SEP)

# The LP logic is inline in try2_real.py (no separate lp_optimizer.py)
lp_file_exists = (ROOT / "lp_optimizer.py").exists()
if lp_file_exists:
    print("  NOTE: lp_optimizer.py exists as a separate file — checking it too.")
    lp_lines = read_lines(ROOT / "lp_optimizer.py")
else:
    print("  NOTE: No separate lp_optimizer.py — LP logic is inline in try2_real.py.")
    lp_lines = main_lines

# a) weekly_budget as an active constraint (prob += spend <= weekly_budget)
active_weekly = [
    (i, ln.strip()) for i, ln in enumerate(lp_lines, 1)
    if re.search(r"prob\s*\+=.*weekly_budget", ln)
    and not ln.strip().startswith("#")
]

# b) weekly_budget commented out
commented_weekly = [
    (i, ln.strip()) for i, ln in enumerate(lp_lines, 1)
    if re.search(r"weekly_budget", ln) and ln.strip().startswith("#")
]

# c) demand-derived caps: total_demand_w / total_demand_s / total_demand_c
demand_cap_hits = find_lines(lp_lines, "total_demand_", is_regex=False)

# d) old hardcoded REUSE dict still active
active_reuse = [
    (i, ln.strip()) for i, ln in enumerate(lp_lines, 1)
    if "REUSE" in ln and not ln.strip().startswith("#")
    and "=" in ln
]

print("  Active weekly_budget constraints (should be 0):")
if active_weekly:
    for ln, txt in active_weekly:
        print(f"    line {ln:5d}: {txt}")
else:
    print("    -- none -- (good)")

print("  Commented-out weekly_budget lines:")
for ln, txt in commented_weekly:
    print(f"    line {ln:5d}: {txt}")

print("  Demand-derived cap lines (total_demand_*):")
for ln, txt in demand_cap_hits:
    print(f"    line {ln:5d}: {txt}")

print("  Active REUSE dict assignments (should be 0 or commented):")
if active_reuse:
    for ln, txt in active_reuse:
        print(f"    line {ln:5d}: {txt}")
else:
    print("    -- none -- (good)")

ok4 = (len(active_weekly) == 0 and len(demand_cap_hits) >= 3)
if ok4:
    print(f"\n{PASS} Weekly budget constraint removed. "
          f"Demand-derived caps ({len(demand_cap_hits)} hits) in place.")
    results["lp_caps"] = (True, f"active_weekly={len(active_weekly)}, "
                                f"demand_caps={len(demand_cap_hits)}")
else:
    issues = []
    if active_weekly:  issues.append(f"{len(active_weekly)} active weekly_budget constraint(s) remain")
    if len(demand_cap_hits) < 3: issues.append("demand-derived caps not found")
    print(f"\n{FAIL} {'; '.join(issues)}")
    results["lp_caps"] = (False, str(issues))


# ──────────────────────────────────────────────────────────────
# CHECK 5 — No CV/DI logic in compute_data_quality()
# ──────────────────────────────────────────────────────────────
print("\n" + SEP)
print("CHECK 5 — No CV/DI logic inside compute_data_quality()")
print(SEP)

# Find the line range of compute_data_quality
dq_start = dq_end = None
for i, ln in enumerate(main_lines, 1):
    if re.match(r"^def compute_data_quality\b", ln):
        dq_start = i
    elif dq_start and i > dq_start and re.match(r"^def \w+", ln):
        dq_end = i - 1
        break
if dq_start and not dq_end:
    dq_end = len(main_lines)

print(f"  compute_data_quality() spans lines {dq_start}–{dq_end}")

# CV/DI patterns inside that function only
cv_di_hits_in_dq = []
if dq_start and dq_end:
    for i in range(dq_start, dq_end + 1):
        ln = main_lines[i - 1]
        stripped = ln.strip()
        if stripped.startswith("#"):
            continue   # skip comments
        if re.search(r"\bcv\b|\bCV\b|\bDI\b|\bcoeff.*var|std\(\).*mean\(\)|mean\(\).*std\(\)", ln, re.I):
            cv_di_hits_in_dq.append((i, stripped))

if cv_di_hits_in_dq:
    print("  CV/DI logic found INSIDE compute_data_quality() — duplicated concern:")
    for ln, txt in cv_di_hits_in_dq:
        print(f"    line {ln:5d}: {txt}")
    print(f"\n{FAIL} Duplicate CV/DI logic present inside compute_data_quality().")
    results["dq_clean"] = (False, cv_di_hits_in_dq)
else:
    print("  No CV, DI, or std/mean variance logic found inside compute_data_quality().")
    print(f"\n{PASS} compute_data_quality() is clean — no freeze logic present.")
    results["dq_clean"] = (True, [])


# ──────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ──────────────────────────────────────────────────────────────
print("\n" + SEP)
print("WIRING VERIFICATION SUMMARY")
print(SEP)

labels = {
    "import":     "CHECK 1  freeze_guard import in try2_real.py",
    "call_order": "CHECK 2  compute_design_freeze() BEFORE clustering",
    "lp_guard":   "CHECK 3  LP status guard (st.error + st.stop)",
    "lp_caps":    "CHECK 4  Weekly cap removed, demand-derived caps",
    "dq_clean":   "CHECK 5  compute_data_quality() free of CV/DI logic",
}

all_ok = True
for key, label in labels.items():
    ok, detail = results.get(key, (False, "not run"))
    icon = PASS if ok else FAIL
    print(f"  {icon}  {label}")
    print(f"         -> {detail}")
    if not ok:
        all_ok = False

print(SEP)
print("  ALL CHECKS PASSED" if all_ok else "  ONE OR MORE CHECKS FAILED")
print(SEP + "\n")
