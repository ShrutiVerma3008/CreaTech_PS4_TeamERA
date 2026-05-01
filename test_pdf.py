import pandas as pd
from utils.report_generator import generate_boq_pdf
from reportlab.lib.pagesizes import A4
import io

boq_df = pd.DataFrame([
    {"sku":"ALU-600","week":1,"procure":10,"reuse":0,
     "hold":0,"idle":2,"week_cost":150000,
     "cumulative_cost":150000},
    {"sku":"ALU-600","week":2,"procure":0,"reuse":8,
     "hold":2,"idle":0,"week_cost":25000,
     "cumulative_cost":175000},
])
delivery_df = pd.DataFrame([
    {"sku":"ALU-600","week":1,"procure":10,
     "estimated_delivery_week":2,"week_cost":150000}
])
metrics = {
    "optimized_cr": 1.49, "baseline_cr": 1.76,
    "savings_cr": 0.27, "savings_pct": 15.3,
    "overall_reuse_rate": 0.65,
    "di_value": 8.2, "di_status": "SAFE"
}
pdf_bytes = generate_boq_pdf(boq_df, delivery_df, 
                              metrics, "Test Tower")
print(f"PDF size: {len(pdf_bytes)} bytes")

pages = pdf_bytes.count(b"/Page\n") + pdf_bytes.count(b"/Page\r\n") + pdf_bytes.count(b"/Page ") + pdf_bytes.count(b"/Page/") - pdf_bytes.count(b"/Pages")
print(f"Pages: {pages}")
