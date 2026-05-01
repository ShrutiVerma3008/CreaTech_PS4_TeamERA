with open('try2_real.py', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if 'Export BoQ' in line or 'download_button' in line:
        print(f'Line {i} indent={len(line)-len(line.lstrip())}: {line.rstrip()}')
