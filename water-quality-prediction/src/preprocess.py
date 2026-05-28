import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

def preprocess_and_resample(file_path="../dataset/pond_iot_2023.csv", freq="1h"):
    """
    Loads the dataset, parses timestamps, resamples to a fixed frequency (freq),
    interpolates gaps, and returns a clean DataFrame.
    """
    print(f"Loading {file_path}...")
    df = pd.read_csv(file_path)
    
    # Parse date
    df['created_date'] = pd.to_datetime(df['created_date'])
    df = df.sort_values('created_date')
    
    # Drop id column
    df = df.drop(columns=['id'])
    
    # Set created_date as index
    df = df.set_index('created_date')
    
    # Resample using mean
    print(f"Resampling to frequency '{freq}'...")
    df_resampled = df.resample(freq).mean()
    
    # Check for missing values after resampling (due to offline gaps)
    missing_before = df_resampled.isnull().sum()
    print(f"Missing values before interpolation:\n{missing_before}")
    
    # Interpolate missing values linearly
    df_resampled = df_resampled.interpolate(method='linear')
    
    # If there are still any NaNs at the beginning, fill them backward
    df_resampled = df_resampled.bfill()
    
    missing_after = df_resampled.isnull().sum()
    print(f"Missing values after interpolation:\n{missing_after}")
    print(f"Resampled dataset size: {df_resampled.shape}")
    
    return df_resampled

def prepare_lstm_data(df, lookback=24, forecast_horizon=1, train_ratio=0.8):
    """
    Scales the features and splits them into training/testing sequences.
    lookback: Number of past time steps to look back (input sequence length)
    forecast_horizon: Number of future time steps to predict
    """
    features = ['water_pH', 'TDS', 'water_temp']
    data = df[features].values
    
    # Scale data to [0, 1] range (crucial for LSTM)
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)
    
    X, y = [], []
    for i in range(len(scaled_data) - lookback - forecast_horizon + 1):
        X.append(scaled_data[i : i + lookback])
        # We predict the 3 target variables at 'i + lookback' up to 'i + lookback + forecast_horizon'
        y.append(scaled_data[i + lookback : i + lookback + forecast_horizon])
        
    X = np.array(X)
    y = np.array(y)
    
    # Reshape y if forecast_horizon is 1 to (N, 3) instead of (N, 1, 3)
    if forecast_horizon == 1:
        y = y.squeeze(axis=1)
        
    # Split into train and test sets chronologically
    train_size = int(len(X) * train_ratio)
    
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    print(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
    
    return X_train, y_train, X_test, y_test, scaler

if __name__ == "__main__":
    df_resampled = preprocess_and_resample()
    X_train, y_train, X_test, y_test, scaler = prepare_lstm_data(df_resampled)
