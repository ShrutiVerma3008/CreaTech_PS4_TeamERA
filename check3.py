import sys; sys.stdout.reconfigure(encoding='utf-8')
with open('docs/DEMO_SCRIPT.md', encoding='utf-8') as f:
    content = f.read()
checks = [
    ('3-Minute', '3-minute timing structure'),
    ('Ibbs (1997)', 'Ibbs citation'),
    ('Peurifoy', 'Peurifoy citation'),
    ('Ester et al', 'DBSCAN citation'),
    ('Hillier', 'LP citation'),
    ('Leys', 'MAD citation'),
    ('15%', 'DI threshold'),
    ('60-80%', 'reuse benchmark'),
    ('30%', 'rework factor'),
    ('IS 1200', 'BoQ standard'),
    ('K-means', 'why not k-means answer'),
    ('BIM', 'BIM question answer'),
]
for term, desc in checks:
    found = term in content
    print(f'{"PASS" if found else "FAIL"} --- {desc}: "{term}"')
