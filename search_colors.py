import sys; sys.stdout.reconfigure(encoding='utf-8')
with open('try2_real.py', encoding='utf-8') as f:
    lines = f.readlines()

print("=== SEARCH 1: color + plotly + template placeholders ===")
for i, line in enumerate(lines, 1):
    if ('color' in line.lower() and
        ('go.' in line or 'plotly' in line.lower() or
         'marker' in line or 'bar' in line.lower()) and
        ('{' in line or 'TEXT' in line)):
        print(f'{i}: {line.rstrip()}')

print("\n=== SEARCH 2: all marker_color / color= in plotly calls ===")
for i, line in enumerate(lines, 1):
    if 'color=' in line and (
        'go.' in line or
        'marker_color' in line or
        'marker=' in line
    ):
        print(f'{i}: {line.rstrip()}')
