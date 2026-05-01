import sys; sys.stdout.reconfigure(encoding='utf-8')
with open('try2_real.py', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Non-f-strings containing {TEXT} {MUTED} {ORANGE} etc passed to Plotly ===")
color_vars = ['{TEXT}', '{MUTED}', '{ORANGE}', '{GREEN}', '{RED}', '{AMBER}', '{TEAL}', '{BLUE}']
for i, line in enumerate(lines, 1):
    # Check if it contains a color placeholder AND is NOT an f-string
    stripped = line.lstrip()
    has_placeholder = any(cv in line for cv in color_vars)
    is_fstring = stripped.startswith('f"') or stripped.startswith("f'") or '=f"' in line or "=f'" in line or '(f"' in line or "(f'" in line
    if has_placeholder and not is_fstring and '"""' not in line and "'''" not in line:
        print(f'{i}: {line.rstrip()}')

print()
print("=== All lines with {TEXT} or {MUTED} in Plotly dicts (title=, font=, annotation) ===")
for i, line in enumerate(lines, 1):
    if ('{TEXT}' in line or '{MUTED}' in line) and ('title' in line or 'font' in line or 'color' in line or 'annotation' in line):
        print(f'{i}: {line.rstrip()}')
