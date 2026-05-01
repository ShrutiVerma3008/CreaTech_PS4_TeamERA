"""
cross_site.py — Cross-Site Formwork Panel Reallocation for FormOptiX
=====================================================================
Identifies idle panels across multiple construction sites and
matches them to demand at other sites to avoid fresh procurement.

Academic basis
--------------
Dania, A.A., Fulford, R., & Hassanain, M.A. (2015).
Performance evaluation of formwork systems in building construction.
Journal of Engineering, Design and Technology, 13(3), 376-399.
-> Cross-site formwork reallocation documented as a cost-reduction
   strategy in large construction firms. Direct business case.

Hanna, A.S. (1998). Concrete Formwork Systems. Marcel Dekker. Ch.4.
-> Panel cycling and logistics. Reuse across sites follows same
   physical constraints as reuse across floors.

Peurifoy, R.L. & Oberlender, G.D. (2010). Formwork for Concrete
Structures (4th ed.). McGraw-Hill. Chapter 7.
-> Industry benchmark: 60-80% reuse rate applies across sites
   when logistics allow.

Public API
----------
collect_idle_panels(site_name, boq_results) -> list
    Returns idle panel records from one site's BoQ results.

match_supply_to_demand(idle_list, demand_list) -> list
    Greedy cross-site match: returns reallocation opportunities.
"""

import copy


# ==============================================================
# FUNCTION 1 — Idle panel collection
# ==============================================================

# Idle panel collection — Dania et al. (2015)
# Cross-site reallocation requires knowing which
# panels are idle at each site each week.
def collect_idle_panels(site_name: str, boq_results: list) -> list:
    """
    Collect rows where idle > 0 from a site's BoQ results.

    Parameters
    ----------
    site_name   : str  — label for this site e.g. "Site A"
    boq_results : list — list of dicts from boq_results;
                  each dict must have keys: sku, week, idle

    Returns
    -------
    list of dicts:
        site     (str)  — site label passed in
        sku      (str)  — panel SKU
        week     (int)  — week number when panels are idle
        idle_qty (int)  — number of idle panels that week

    Academic basis
    --------------
    Dania et al. (2015): idle panels on one site represent
    capital tied up that can be unlocked by reallocation.
    """
    results = []
    for row in boq_results:
        idle_qty = row.get("idle", 0)
        if idle_qty and idle_qty > 0:
            results.append({
                "site":     site_name,
                "sku":      row.get("sku", ""),
                "week":     row.get("week", 0),
                "idle_qty": int(idle_qty),
            })
    return results


# ==============================================================
# FUNCTION 2 — Greedy cross-site supply-demand match
# ==============================================================

# Greedy cross-site match — Dania et al. (2015)
# First-fit allocation: find first available idle batch
# that satisfies SKU, timing, and quantity constraints.
# Not optimal — a full LP across sites would be optimal
# but is out of scope for this prototype.
# Reference for optimal formulation:
# Biruk & Jaskowski (2017) — multi-resource LP.
def match_supply_to_demand(idle_list: list, demand_list: list) -> list:
    """
    Greedy match of idle panels (supply) to procurement needs (demand).

    Parameters
    ----------
    idle_list   : list — output of collect_idle_panels() combined
                  across all sites. Each dict: site, sku, week, idle_qty
    demand_list : list — procurement needs per site. Each dict:
                  site, sku, week, procure_qty

    Matching rules
    --------------
    For each demand row (site_B, sku, week_needed, qty):
      Find idle row where:
        - idle["sku"]      == demand["sku"]         (same SKU)
        - idle["site"]     != demand["site"]        (different site)
        - idle["week"]     <= demand["week"] - 1    (available before)
        - idle["idle_qty"] >= qty_needed            (enough panels)
      Take first match (greedy / first-fit).
      Reduce idle["idle_qty"] by qty_needed to prevent double-allocation.

    Returns
    -------
    list of dicts per match:
        from_site       (str) — site supplying panels
        to_site         (str) — site receiving panels
        sku             (str) — panel SKU
        qty             (int) — panels transferred
        available_week  (int) — week panels are idle at from_site
        needed_week     (int) — week panels needed at to_site
        saving_rs       (float) — set to 0.0; caller sets c_p * qty

    Academic basis
    --------------
    Dania et al. (2015): cross-site reallocation avoids fresh
    procurement cost equal to qty x procurement price per panel.
    Hanna (1998) Ch.4: physical transport constraint requires
    panels available at least 1 week before needed.
    """
    # Deep-copy idle_list so callers dict is not mutated
    working_idle = copy.deepcopy(idle_list)

    matches = []
    for demand in demand_list:
        site_d  = demand["site"]
        sku_d   = demand["sku"]
        week_d  = demand["week"]
        qty_d   = demand.get("procure_qty", 0)

        if qty_d <= 0:
            continue

        for idle in working_idle:
            if (
                idle["sku"]      == sku_d
                and idle["site"] != site_d               # different site
                and idle["week"] <= week_d - 1           # available before
                and idle["idle_qty"] >= qty_d            # enough panels
            ):
                matches.append({
                    "from_site":      idle["site"],
                    "to_site":        site_d,
                    "sku":            sku_d,
                    "qty":            int(qty_d),
                    "available_week": idle["week"],
                    "needed_week":    week_d,
                    "saving_rs":      0.0,  # caller multiplies qty x c_p
                })
                # Reduce idle pool to prevent double-allocation
                idle["idle_qty"] -= qty_d
                break  # first-fit: move to next demand row

    return matches


# ==============================================================
# STEP 5 — Standalone test
# ==============================================================

if __name__ == "__main__":
    # Test: Site A has idle ALU-600 in week 3
    #       Site B needs ALU-600 in week 5
    # Expected: 1 match found

    idle = [
        {"site": "Site A", "sku": "ALU-600",
         "week": 3, "idle_qty": 50},
        {"site": "Site A", "sku": "ALU-450",
         "week": 4, "idle_qty": 30},
    ]
    demand = [
        {"site": "Site B", "sku": "ALU-600",
         "week": 5, "procure_qty": 40},
        {"site": "Site C", "sku": "ALU-450",
         "week": 6, "procure_qty": 25},
    ]
    matches = match_supply_to_demand(idle, demand)
    print(f"Matches found: {len(matches)}")
    for m in matches:
        print(m)
    assert len(matches) == 2, f"Expected 2, got {len(matches)}"
    assert matches[0]["from_site"] == "Site A"
    assert matches[0]["to_site"]   == "Site B"
    assert matches[1]["from_site"] == "Site A"
    assert matches[1]["to_site"]   == "Site C"
    print("Standalone test PASSED")
