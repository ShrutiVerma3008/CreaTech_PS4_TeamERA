with open('try2_real.py', encoding='utf-8') as f:
    lines = f.readlines()
targets = ['di_value', 'di_status', 'overall_reuse_rate']
for i, line in enumerate(lines, 1):
    for t in targets:
        if f'session_state["{t}"]' in line or \
           f'session_state.{t}' in line:
            print(f'Line {i}: {line.rstrip()}')
