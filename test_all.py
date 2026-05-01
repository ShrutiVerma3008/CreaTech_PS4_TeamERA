import sys
import ast

sys.stdout.reconfigure(encoding='utf-8')

def print_header(title):
    print(f"\\n{'='*40}\\n{title}\\n{'='*40}")

# CHECK 1
print_header("CHECK 1")
sys.path.insert(0, '.')
from core.cross_site import collect_idle_panels
boq = [
    {'sku':'ALU-600','week':1,'procure':10,'reuse':0,
     'hold':0,'idle':0,'week_cost':150000},
    {'sku':'ALU-600','week':2,'procure':0,'reuse':8,
     'hold':2,'idle':5,'week_cost':25000},
    {'sku':'ALU-450','week':3,'procure':5,'reuse':0,
     'hold':0,'idle':0,'week_cost':75000},
]
result = collect_idle_panels('Site A', boq)
print(f'Idle rows: {len(result)}')
for r in result: print(r)
assert len(result) == 1, f'Expected 1, got {len(result)}'
assert result[0]['site'] == 'Site A'
assert result[0]['sku']  == 'ALU-600'
assert result[0]['week'] == 2
assert result[0]['idle_qty'] == 5
print('collect_idle_panels PASS')

# CHECK 2
print_header("CHECK 2")
from core.cross_site import match_supply_to_demand
idle = [{'site':'Site A','sku':'ALU-600',
         'week':3,'idle_qty':50}]
demand = [{'site':'Site A','sku':'ALU-600',
           'week':5,'procure_qty':40}]
matches = match_supply_to_demand(idle, demand)
print(f'Matches: {len(matches)}')
assert len(matches) == 0, \
    f'Same-site match must be prevented, got {len(matches)}'
print('Same-site prevention PASS')

# CHECK 3
print_header("CHECK 3")
idle = [{'site':'Site A','sku':'ALU-600',
         'week':5,'idle_qty':50}]
demand = [{'site':'Site B','sku':'ALU-600',
           'week':5,'procure_qty':40}]
matches = match_supply_to_demand(idle, demand)
print(f'Same-week matches: {len(matches)}')
assert len(matches) == 0, \
    f'Timing constraint failed, got {len(matches)}'

idle2 = [{'site':'Site A','sku':'ALU-600',
          'week':4,'idle_qty':50}]
matches2 = match_supply_to_demand(idle2, demand)
print(f'Week-before matches: {len(matches2)}')
assert len(matches2) == 1, \
    f'Expected 1 match, got {len(matches2)}'
print('Timing constraint PASS')

# CHECK 4
print_header("CHECK 4")
idle = [{'site':'Site A','sku':'ALU-600',
         'week':3,'idle_qty':50}]
demand = [
    {'site':'Site B','sku':'ALU-600',
     'week':5,'procure_qty':40},
    {'site':'Site C','sku':'ALU-600',
     'week':5,'procure_qty':40},
]
matches = match_supply_to_demand(idle, demand)
print(f'Matches: {len(matches)}')
print(f'Match qtys: {[m["qty"] for m in matches]}')
assert len(matches) == 1, \
    f'Expected 1 match (not 2), got {len(matches)}'
assert matches[0]['qty'] == 40
print('Double-allocation prevention PASS')

# CHECK 5
print_header("CHECK 5")
with open('try2_real.py', encoding='utf-8') as f:
    lines = f.readlines()
count = 0
for i, line in enumerate(lines, 1):
    if 'st.tabs(' in line:
        print(f'Line {i}: {line.rstrip()}')
        count += 1
    elif 'Multi-Site' in line or 'multi_site' in line.lower():
        print(f'Line {i}: {line.rstrip()}')
        count += 1
    if count >= 20: break

# CHECK 6
print_header("CHECK 6")
for i, line in enumerate(lines, 1):
    if 'export_json' in line or 'download_json_btn' in line \
       or 'BoQ JSON' in line:
        indent = len(line) - len(line.lstrip())
        print(f'Line {i} indent={indent}: {line.rstrip()}')

# CHECK 7
print_header("CHECK 7")
for i, line in enumerate(lines, 1):
    if 'cross_site' in line:
        print(f'Line {i}: {line.rstrip()}')

# CHECK 8
print_header("CHECK 8")
with open('core/cross_site.py', encoding='utf-8') as f:
    content = f.read()
citations = ['Dania', 'Hanna', 'Biruk']
for c in citations:
    print(f'{c}: {"FOUND" if c in content else "MISSING"}')

# CHECK 9
print_header("CHECK 9")
for f in ['core/cross_site.py', 'try2_real.py']:
    ast.parse(open(f, encoding='utf-8').read())
    print(f'SYNTAX OK  {f}')

# CHECK 11
print_header("CHECK 11")
src = open('try2_real.py', encoding='utf-8').read()
ast.parse(src)

lines = src.split('\\n')
tab6_start = None
for i, line in enumerate(lines):
    if 'with tab6:' in line:
        tab6_start = i
        break

if tab6_start is None:
    print('FAIL: with tab6: not found')
else:
    print(f'tab6 starts at line {tab6_start + 1}')
    for name in ['collect_idle_panels', 'match_supply_to_demand']:
        for i, line in enumerate(lines):
            if name in line and i < tab6_start:
                print(f'WARNING: {name} appears before tab6 at line {i+1}')
                break
        else:
            print(f'{name}: only in tab6 block — OK')
