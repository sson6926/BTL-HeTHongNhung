import pandas as pd
import numpy as np
import os

def profile_data():
    file_path = "dataset/pond_iot_2023.csv"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} does not exist!")
        return

    print("--- Loading Dataset ---")
    df = pd.read_csv(file_path)
    print(f"Shape: {df.shape}")
    print("\n--- Columns & Data Types ---")
    print(df.dtypes)
    
    print("\n--- First 5 rows ---")
    print(df.head())
    
    print("\n--- Missing Values ---")
    print(df.isnull().sum())
    
    # Parse date
    print("\n--- Parsing Timestamps ---")
    df['created_date'] = pd.to_datetime(df['created_date'])
    df = df.sort_values('created_date')
    
    start_date = df['created_date'].min()
    end_date = df['created_date'].max()
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    print(f"Duration: {end_date - start_date}")
    
    # Check frequency
    print("\n--- Time gaps analysis ---")
    time_diffs = df['created_date'].diff().dropna()
    print(f"Average gap between consecutive readings: {time_diffs.mean()}")
    print(f"Median gap: {time_diffs.median()}")
    print(f"Min gap: {time_diffs.min()}")
    print(f"Max gap: {time_diffs.max()}")
    
    # Value ranges
    print("\n--- Value Statistics ---")
    print(df[['water_pH', 'TDS', 'water_temp']].describe())

if __name__ == "__main__":
    profile_data()
