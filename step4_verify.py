import sys, ast; sys.stdout.reconfigure(encoding='utf-8')

# Syntax check
ast.parse(open('try2_real.py', encoding='utf-8').read())
print('SYNTAX OK  try2_real.py')

# Verify no more literal {TEXT} in Plotly color dicts
with open('try2_real.py', encoding='utf-8') as f:
    lines = f.readlines()
hits = []
for i, line in enumerate(lines, 1):
    if 'color="{TEXT}"' in line or "color='{TEXT}'" in line:
        hits.append(f'{i}: {line.rstrip()}')
if hits:
    print('REMAINING LITERAL {TEXT} in color fields:')
    for h in hits: print(h)
else:
    print('CLEAN: no more literal {TEXT} in color= fields')

# Verify specific fixed lines
for i, line in enumerate(lines, 1):
    if i in (416, 2361):
        print(f'Line {i}: {line.rstrip()}')
