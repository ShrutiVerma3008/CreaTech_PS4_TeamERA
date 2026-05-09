import pandas as pd
import os

file_path = r"d:\sem_6\creaTech\try1\data\demo_tower_40floors.xlsx"

try:
    print(f"Attempting to read: {file_path}")
    
    # Read floors sheet
    df_floors = pd.read_excel(file_path, sheet_name='floors')
    print("\n'floors' sheet loaded successfully:")
    print(df_floors.head())
    
    # Read schedule sheet
    df_schedule = pd.read_excel(file_path, sheet_name='schedule')
    print("\n'schedule' sheet loaded successfully:")
    print(df_schedule.head())

except Exception as e:
    print(f"\nError reading file: {e}")
