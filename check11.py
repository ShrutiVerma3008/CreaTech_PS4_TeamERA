with open('utils/report_generator.py', encoding='utf-8') as f:
    content = f.read()
citations = ['IS 1200', 'PMBOK', 'Ester et al', 
             'Hillier', 'Ibbs', 'ACI 347R-14']
for c in citations:
    found = c in content
    print(f'{c}: {"FOUND" if found else "MISSING"}'  )
