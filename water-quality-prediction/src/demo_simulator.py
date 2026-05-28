import time
import os
import pandas as pd
import numpy as np
import pickle
import torch

from model import WaterQualityLSTM
from preprocess import preprocess_and_resample
from predict import forecast_future

def run_simulation(speed_seconds=2.0):
    """
    Simulates a live IoT stream in fast-forward mode.
    Every `speed_seconds` real-time seconds, 1 hour of simulated time passes.
    The LSTM model uses the sliding window of the last 24 hours to forecast the next 12 hours.
    """
    # 1. Load weights and scaler
    model_path = "../artifacts/lstm_water_quality.pth"
    scaler_path = "../artifacts/scaler.pkl"
    
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        print("Error: Trained model assets not found! Please run train.py first.")
        return
        
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = WaterQualityLSTM(input_size=3, hidden_size=64, num_layers=2, output_size=3, dropout=0.2)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    # 2. Load resampled data
    df_resampled = preprocess_and_resample()
    
    # We will simulate starting from the test set area (e.g. last 150 hours of the dataset)
    start_index = len(df_resampled) - 150
    lookback = 24
    forecast_steps = 12
    
    print("\n" + "="*60)
    print("🚀 KHỞI CHẠY HỆ THỐNG GIẢ LẬP TUA NHANH THỜI GIAN (IoT SIMULATOR)")
    print(f"Tần suất mô phỏng: 1 giờ dữ liệu = {speed_seconds} giây thực tế.")
    print("="*60)
    time.sleep(2)
    
    try:
        for idx in range(start_index, len(df_resampled) - forecast_steps):
            # Clear console for neat output
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Extract sliding lookback window
            current_window = df_resampled.iloc[idx - lookback + 1 : idx + 1]
            current_time = current_window.index[-1]
            
            # Extract current actual values
            curr_val = current_window.iloc[-1]
            pH_now = curr_val['water_pH']
            TDS_now = curr_val['TDS']
            temp_now = curr_val['water_temp']
            
            # 3. Forecast the next 12 steps
            future_vals = forecast_future(model, scaler, device, current_window.values, steps=forecast_steps)
            
            # Print beautiful ASCII Dashboard
            print("┌" + "─"*58 + "┐")
            print(f"│  📡 THỜI GIAN GIẢ LẬP (IoT): {current_time.strftime('%Y-%m-%d %H:%M:%S')}  │")
            print("├" + "─"*58 + "┤")
            print("│  📊 CHỈ SỐ CẢM BIẾN HIỆN TẠI (REAL-TIME SENSORS):        │")
            print(f"│    - pH Nước (water_pH):    {pH_now:.2f}                         │")
            print(f"│    - Độ sạch (TDS):         {TDS_now:.1f} ppm                    │")
            print(f"│    - Nhiệt độ (water_temp): {temp_now:.2f} °C                   │")
            print("├" + "─"*58 + "┤")
            print("│  🔮 DỰ BÁO TỪ LSTM CHO 6 GIỜ TIẾP THEO (FORECAST):       │")
            
            for step in range(6):
                pred_hour = current_time + pd.Timedelta(hours=step + 1)
                p_pH = future_vals[step, 0]
                p_TDS = future_vals[step, 1]
                p_temp = future_vals[step, 2]
                print(f"│    {pred_hour.strftime('%H:%M')} -> pH: {p_pH:.2f} | TDS: {p_TDS:.1f} ppm | Temp: {p_temp:.2f} °C │")
                
            print("└" + "─"*58 + "┘")
            print("\n* Nhấn Ctrl+C để dừng mô phỏng...")
            
            # Wait for next step
            time.sleep(speed_seconds)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Đã dừng chương trình mô phỏng IoT.")

if __name__ == "__main__":
    run_simulation(speed_seconds=2.0)
