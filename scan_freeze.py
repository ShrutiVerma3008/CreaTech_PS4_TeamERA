import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('try2_real.py', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    lo = line.lower()
    if 'freeze' in lo or 'di_value' in lo or 'compute_design' in lo or 'freeze_guard' in lo or 'FREEZE_GUARD' in line:
        print(f'{i}: {line.rstrip()}')
