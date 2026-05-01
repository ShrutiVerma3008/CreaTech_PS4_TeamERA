import sys, ast, os; sys.stdout.reconfigure(encoding='utf-8')
files = [
    'try2_real.py',
    'freeze_guard.py',        # lives at root, not core/
    'core/clustering.py',
    'core/lp_optimizer.py',
    'core/cross_site.py',
    'utils/data_loader.py',
    'utils/report_generator.py',
]
all_ok = True
for f in files:
    if not os.path.exists(f):
        print(f'MISSING: {f}')
        all_ok = False
        continue
    try:
        ast.parse(open(f, encoding='utf-8').read())
        print(f'SYNTAX OK  {f}')
    except SyntaxError as e:
        print(f'SYNTAX ERR {f}: {e}')
        all_ok = False
print('ALL SYNTAX OK' if all_ok else 'SYNTAX ERRORS FOUND')
