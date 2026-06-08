import os
import torch
import numpy as np
import pandas as pd
import pickle
from datetime import timedelta

from model import WaterQualityLSTM, WaterQualityGRU, WaterQualitySeq2Seq

def load_model(model_name="lstm", model_path=None, scaler_path="../artifacts/scaler.pkl"):
    """
    Loads the trained model weights and the MinMaxScaler.
    """
    if model_path is None:
        if model_name == "lstm":
            model_path = "../artifacts/lstm_water_quality.pth"
        elif model_name == "gru":
            model_path = "../artifacts/gru_water_quality.pth"
        elif model_name == "seq2seq":
            model_path = "../artifacts/seq2seq_water_quality.pth"
        elif model_name == "xgboost":
            model_path = "../artifacts/xgboost_model.pkl"
            
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Model weights ({model_path}) or scaler file ({scaler_path}) not found. Please train the model first by running train.py.")
        
    # Load scaler
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
        
    # Load model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    if model_name == "xgboost":
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        print(f"Forecaster (XGBOOST) loaded successfully.")
        return model, scaler, device
        
    elif model_name == "lstm":
        model = WaterQualityLSTM(input_size=3, hidden_size=64, num_layers=2, output_size=3, dropout=0.2)
    elif model_name == "gru":
        model = WaterQualityGRU(input_size=3, hidden_size=64, num_layers=2, output_size=3, dropout=0.2)
    elif model_name == "seq2seq":
        model = WaterQualitySeq2Seq(input_size=3, hidden_size=64, num_layers=2, output_size=3, forecast_horizon=12, dropout=0.2)
    else:
        raise ValueError(f"Unknown model name: {model_name}")
        
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    print(f"Forecaster ({model_name.upper()}) loaded successfully on: {device}")
    return model, scaler, device

def predict(model, scaler, device, last_sequence, steps=24, model_name="lstm"):
    """
    Forecasts future values.
    - last_sequence: numpy array of shape (lookback, 3) containing the most recent unscaled data.
    - steps: number of steps (hours) to forecast in the future.
    """
    # Scale the input sequence
    scaled_seq = scaler.transform(last_sequence)
    
    if model_name == "xgboost":
        current_seq = scaled_seq.copy()
        predictions = []
        for i in range(steps):
            # Flatten current sequence: shape (1, 72)
            input_flat = current_seq.reshape(1, -1)
            pred_np = model.predict(input_flat)[0] # shape: (3,)
            predictions.append(pred_np)
            
            # Slide window: append prediction and discard oldest step
            current_seq = np.vstack([current_seq[1:], pred_np])
            
        # Inverse scale all predictions
        predictions = np.array(predictions)
        inv_predictions = scaler.inverse_transform(predictions)
        return inv_predictions
        
    elif model_name == "seq2seq":
        # Seq2Seq outputs forecast_horizon (12) steps directly
        current_seq = scaled_seq.copy()
        predictions = []
        
        # Block-autoregressive loop for arbitrary forecast steps
        steps_predicted = 0
        while steps_predicted < steps:
            input_tensor = torch.tensor(current_seq, dtype=torch.float32).unsqueeze(0).to(device)
            with torch.no_grad():
                # Output shape: (1, 12, 3)
                pred = model(input_tensor, teacher_forcing_ratio=0.0)
            pred_np = pred.cpu().numpy()[0] # shape: (12, 3)
            
            # Append predictions
            predictions.extend(pred_np)
            steps_predicted += len(pred_np)
            
            # Slide window by 12 steps
            current_seq = np.vstack([current_seq[len(pred_np):], pred_np])
            
        # Slice to requested steps
        predictions = np.array(predictions[:steps])
        inv_predictions = scaler.inverse_transform(predictions)
        return inv_predictions
        
    else: # lstm or gru
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

def test_prediction(model_name="lstm", forecast_steps=12):
    # 1. Load trained assets
    try:
        model, scaler, device = load_model(model_name=model_name)
    except FileNotFoundError as e:
        print(e)
        return
        
    # 2. Extract the last 24 hours of data from the raw CSV
    print("\nReading recent data for prediction input...")
    csv_path = "../dataset/test.csv"
    if not os.path.exists(csv_path):
        csv_path = "../dataset/train.csv"
        
    df = pd.read_csv(csv_path)
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
    
    # 3. Forecast the next hours
    print(f"\nForecasting next {forecast_steps} hours into the future using {model_name.upper()}...")
    future_vals = predict(model, scaler, device, recent_sequence.values, steps=forecast_steps, model_name=model_name)
    
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
    import argparse
    parser = argparse.ArgumentParser(description="Run predictions with trained models.")
    parser.add_argument("--model", type=str, default="lstm", choices=["lstm", "gru", "seq2seq", "xgboost"],
                        help="Model to use (lstm, gru, seq2seq, xgboost)")
    parser.add_argument("--steps", type=int, default=12, help="Steps to forecast (default 12)")
    args = parser.parse_args()
    
    test_prediction(model_name=args.model, forecast_steps=args.steps)