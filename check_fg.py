import sys, os; sys.stdout.reconfigure(encoding='utf-8')
# freeze_guard location check
for root, dirs, files in os.walk('.'):
    for fn in files:
        if fn == 'freeze_guard.py':
            print(f'Found: {os.path.join(root, fn)}')
