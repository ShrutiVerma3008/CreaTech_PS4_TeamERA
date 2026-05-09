import pandas as pd

file_path = r"d:\sem_6\creaTech\try1\data\demo_tower_40floors.xlsx"

try:
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    print("Content of Sheet1:")
    print(df.head(20))
    print("\nColumns:", df.columns.tolist())
except Exception as e:
    print(f"Error: {e}")
