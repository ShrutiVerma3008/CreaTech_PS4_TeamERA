import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('try2_real.py', encoding='utf-8') as f:
    src = f.read()

checks = [
    ('predict_design_change_risk in import', 'predict_design_change_risk' in src),
    ('di_history in session_state init block', '"di_history" not in st.session_state' in src),
    ('di_history cap at 5', 'st.session_state["di_history"][-5:]' in src),
    ('Design change trend prediction subheader', 'st.subheader("Design change trend prediction")' in src),
    ('_RISK_FN dict present', '_RISK_FN = {' in src),
    ('DI trend metric label', '"DI trend"' in src),
    ('Prediction confidence metric label', '"Prediction confidence"' in src),
    ('line_chart called', 'st.line_chart(_hist_df' in src),
    ('st.caption(_pred["citation"])', 'st.caption(_pred["citation"])' in src),
]

all_pass = True
for label, ok in checks:
    print(f"{label}: {'PASS' if ok else 'FAIL'}")
    if not ok: all_pass = False

sys.exit(0 if all_pass else 1)
