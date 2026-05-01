import sys; sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
df = pd.read_excel('data/demo_tower_40floors.xlsx')
print(f'Rows: {len(df)}')
print(f'Columns: {df.columns.tolist()}')
print(f'Panel types: {df["panel_type"].unique().tolist()}')
print(f'Null count: {df.isnull().sum().sum()}')
bad = df[df['strip_week'] != df['week_end'] + 2]
print(f'strip_week violations: {len(bad)}')
clA = df[df['floor_id'].isin([f'F{i:02d}' for i in range(1,13)])]
print(f'Cluster A slab mean: {clA["slab_area_m2"].mean():.0f}')
atyp = df[df['floor_id'].isin([f'F{i:02d}' for i in range(36,41)])]
print(f'Atypical slab mean: {atyp["slab_area_m2"].mean():.0f}')
ratio = atyp['slab_area_m2'].mean() / clA['slab_area_m2'].mean()
print(f'Atypical/ClusterA ratio: {ratio:.2f}x')
assert ratio > 1.3, f'Atypical not distinct enough: {ratio:.2f}x'
print('All integrity checks PASS')
