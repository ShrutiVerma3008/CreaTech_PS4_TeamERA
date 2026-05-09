import pandas as pd

file_path = r"d:\sem_6\creaTech\try1\data\demo_tower_40floors.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    print(f"Sheets found in {file_path}:")
    print(xl.sheet_names)
except Exception as e:
    print(f"Error: {e}")
