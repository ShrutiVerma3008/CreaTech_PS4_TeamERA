import sys, os; sys.stdout.reconfigure(encoding='utf-8')
files_to_check = [
    'try2_real.py',
    'README.md',
    'core/lp_optimizer.py',
    'core/clustering.py',
    'freeze_guard.py',          # lives at root
    'utils/report_generator.py',
]
for fpath in files_to_check:
    if not os.path.exists(fpath):
        print(f'SKIP (not found): {fpath}')
        continue
    with open(fpath, encoding='utf-8') as f:
        content = f.read()
    if '97.3' in content:
        lns = content.split('\n')
        for i, l in enumerate(lns, 1):
            if '97.3' in l:
                print(f'FOUND {fpath} line {i}: {l.strip()}')
    else:
        print(f'CLEAN: {fpath}')
