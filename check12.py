from utils.report_generator import generate_boq_pdf
import pandas as pd
boq = pd.DataFrame([
  {'sku':'ALU-600','week':1,'procure':10,'reuse':0,
   'hold':0,'idle':0,'week_cost':150000,
   'cumulative_cost':150000}
])
dlv = pd.DataFrame([
  {'sku':'ALU-600','week':1,'procure':10,
   'estimated_delivery_week':2,'week_cost':150000}
])
m = {'optimized_cr':1.49,'baseline_cr':1.76,
     'savings_cr':0.27,'savings_pct':15.3,
     'overall_reuse_rate':0.65,
     'di_value':8.2,'di_status':'SAFE'}
pdf = generate_boq_pdf(boq, dlv, m, 'Tower A')
assert isinstance(pdf, bytes), 'Not bytes'
assert len(pdf) > 5000, f'Too small: {len(pdf)}'
print(f'PASS — PDF bytes: {len(pdf)}')
