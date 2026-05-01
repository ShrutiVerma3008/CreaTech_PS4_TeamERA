with open('try2_real.py', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if 'project_name' in line and \
       ('text_input' in line or 'generate_boq_pdf' in line):
        print(f'Line {i}: {line.rstrip()}')
