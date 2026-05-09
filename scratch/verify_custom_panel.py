"""Verify Step 5 checklist for Standard vs Custom Panel Analysis."""
src  = open("try2_real.py", encoding="utf-8").read()
pdf  = open("utils/report_generator.py", encoding="utf-8").read()

checks = [
    ("standard_pct column added after validate_and_map",   src,  'df_raw["standard_pct"]'),
    ("custom_area_m2 column added",                         src,  'df_raw["custom_area_m2"]'),
    ("div-by-zero guard on slab_area_m2",                   src,  "max(row[\"slab_area_m2\"], 1)"),
    ("session_state standard_pct_avg stored",               src,  'st.session_state["standard_pct_avg"]'),
    ("session_state custom_area_total stored",              src,  'st.session_state["custom_area_total"]'),
    ("session_state custom_cost_premium stored",            src,  'st.session_state["custom_cost_premium"]'),
    ('PDF metrics uses .get("custom_area_total",0)',         src,  '"custom_area_total":   st.session_state.get'),
    ('PDF metrics uses .get("custom_cost_premium",0)',       src,  '"custom_cost_premium": st.session_state.get'),
    ("Expander label correct",                              src,  "Standard vs Custom Panel Analysis"),
    ("High-risk filter < 70",                               src,  'standard_pct"] < 70.0'),
    ("bar_chart y=standard_pct",                            src,  'y="standard_pct"'),
    ("Peurifoy caption present",                            src,  "Peurifoy"),
    ("PDF custom panel area row (Rs, not rupee sign)",      pdf,  '"Custom Panel Area"'),
    ("PDF custom cost premium row",                         pdf,  '"Custom Cost Premium"'),
    ("PDF uses Rs prefix not rupee sign",                   pdf,  '"Rs " + str(round'),
    ("PDF di_row index offset for 2 new rows",              pdf,  "len(rows) - 3"),
    ("PDF .get custom_area_total with default 0",           pdf,  'metrics.get("custom_area_total", 0)'),
    ("PDF .get custom_cost_premium with default 0",         pdf,  'metrics.get("custom_cost_premium", 0)'),
]

all_pass = True
for label, text, needle in checks:
    ok = needle in text
    print(f"{'PASS' if ok else 'FAIL'} | {label}")
    if not ok:
        all_pass = False

print()
print("All checks passed!" if all_pass else "One or more checks FAILED.")
