import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('try2_real.py', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if 'c_p' in line and ('number_input' in line or 'sidebar' in line or 'session_state' in line):
        print(f'{i}: {line.rstrip()}')
