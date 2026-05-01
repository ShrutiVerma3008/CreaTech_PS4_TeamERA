with open('freeze_guard.py', encoding='utf-8') as f:
    content = f.read()
citations = ['Montgomery', 'Ibbs', '2.5', '0.30', '0.80', 'Leys']
for c in citations:
    print(f"{c}: {'FOUND' if c in content else 'MISSING'}")
