import os
import torch
import numpy as np
import pandas as pd
import pickle
from datetime import timedelta

from model import WaterQualityLSTM

def load_model(model_path="../artifacts/lstm_water_quality.pth", scaler_path="../artifacts/scaler.pkl"):
    """
    Loads the trained model weights and the MinMaxScaler.
    """
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        raise FileNotFoundError("Model weights or scaler file not found. Please train the model first by running train.py.")
        
    # Load scaler
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
        
    # Load model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = WaterQualityLSTM(input_size=3, hidden_size=64, num_layers=2, output_size=3, dropout=0.2)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    print(f"Forecaster loaded successfully on: {device}")
    return model, scaler, device

def predict(model, scaler, device, last_sequence, steps=24):
    """
    Forecasts future values autoregressively.
    - last_sequence: numpy array of shape (lookback, 3) containing the most recent unscaled data.
    - steps: number of steps (hours) to forecast in the future.
    """
    # Scale the input sequence
    scaled_seq = scaler.transform(last_sequence)
    
    current_seq = scaled_seq.copy()
    predictions = []
    
    for i in range(steps):
        # Convert to tensor and add batch dimension: shape (1, lookback, 3)
        input_tensor = torch.tensor(current_seq, dtype=torch.float32).unsqueeze(0).to(device)
        
        with torch.no_grad():
            pred = model(input_tensor) # output shape: (1, 3)
            
        pred_np = pred.cpu().numpy()[0] # shape: (3,)
        predictions.append(pred_np)
        
        # Slide window: append prediction and discard oldest step
        current_seq = np.vstack([current_seq[1:], pred_np])
        
    # Inverse scale all predictions
    predictions = np.array(predictions)
    inv_predictions = scaler.inverse_transform(predictions)
    
    return inv_predictions

def test_prediction():
    # 1. Load trained assets
    try:
        model, scaler, device = load_model()
    except FileNotFoundError as e:
        print(e)
        return
        
    # 2. Extract the last 24 hours of data from the raw CSV
    print("\nReading recent data for prediction input...")
    df = pd.read_csv("../dataset/pond_iot_2023.csv")
    df['created_date'] = pd.to_datetime(df['created_date'])
    df = df.sort_values('created_date')
    df = df.drop(columns=['id']).set_index('created_date')
    
    # Resample and interpolate to match training format
    df_resampled = df.resample("1h").mean().interpolate(method='linear').bfill()
    
    # Grab the last 24 records (one full day)
    lookback = 24
    recent_sequence = df_resampled.tail(lookback)
    last_timestamp = recent_sequence.index[-1]
    
    print(f"Input sequence time range: {recent_sequence.index[0]} to {last_timestamp}")
    print("Recent physical measurements (last 3 hours):")
    print(recent_sequence.tail(3))
    
    # 3. Forecast the next 12 hours
    forecast_steps = 12
    print(f"\nForecasting next {forecast_steps} hours into the future...")
    future_vals = predict(model, scaler, device, recent_sequence.values, steps=forecast_steps)
    
    # Create a nice DataFrame representing the forecast
    forecast_times = [last_timestamp + timedelta(hours=i+1) for i in range(forecast_steps)]
    forecast_df = pd.DataFrame(future_vals, columns=['water_pH', 'TDS', 'water_temp'], index=forecast_times)
    forecast_df.index.name = "forecast_date"
    
    print("\n=== Forecast Results ===")
    print(forecast_df)
    
    # Save the forecast results
    forecast_df.to_csv("../artifacts/future_forecast_12h.csv")
    print("\nForecast results saved to artifacts/future_forecast_12h.csv")

if __name__ == "__main__":
    test_prediction()
    # model, scaler, device = load_model()