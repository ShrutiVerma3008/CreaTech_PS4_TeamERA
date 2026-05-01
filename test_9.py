import ast
files = ['freeze_guard.py', 'try2_real.py']
for f in files:
    ast.parse(open(f, encoding='utf-8').read())
    print(f'SYNTAX OK  {f}')
