import os
import sys
import torch
import numpy as np

# Reconfigure stdout to use UTF-8
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import pickle
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from torch.utils.data import Dataset, DataLoader

from preprocess import preprocess_and_resample, prepare_lstm_data
from predict import load_model, predict

# Custom PyTorch Dataset for evaluation
class WaterQualityDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

def evaluate_models():
    print("=== STARTING MODEL COMPARISON EVALUATION ===")
    
    # 1. Load data
    df_resampled = preprocess_and_resample()
    
    # We load two formats: 1-step (for LSTM, GRU, XGBoost) and 12-step (for Seq2Seq)
    X_train_1, y_train_1, X_test_1, y_test_1, scaler = prepare_lstm_data(df_resampled, forecast_horizon=1)
    X_train_12, y_train_12, X_test_12, y_test_12, _ = prepare_lstm_data(df_resampled, forecast_horizon=12)
    
    models_to_evaluate = ["lstm", "gru", "seq2seq", "xgboost"]
    results = {}
    
    for name in models_to_evaluate:
        print(f"\nEvaluating model: {name.upper()}...")
        
        # Determine paths
        if name == "lstm":
            path = "../artifacts/lstm_water_quality.pth"
        elif name == "gru":
            path = "../artifacts/gru_water_quality.pth"
        elif name == "seq2seq":
            path = "../artifacts/seq2seq_water_quality.pth"
        elif name == "xgboost":
            path = "../artifacts/xgboost_model.pkl"
            
        if not os.path.exists(path):
            print(f"Warning: Weights for model '{name}' not found at {path}. Skipping evaluation.")
            continue
            
        # Load model assets
        try:
            model, _, device = load_model(model_name=name, model_path=path, scaler_path="../artifacts/scaler.pkl")
        except Exception as e:
            print(f"Error loading {name.upper()} model: {e}")
            continue
            
        if name == "xgboost":
            # Flatten X_test
            X_test_flat = X_test_1.reshape(X_test_1.shape[0], -1)
            all_predictions = model.predict(X_test_flat)
            all_actuals = y_test_1
            
            inv_predictions = scaler.inverse_transform(all_predictions)
            inv_actuals = scaler.inverse_transform(all_actuals)
            
        elif name == "seq2seq":
            test_dataset = WaterQualityDataset(X_test_12, y_test_12)
            test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
            
            all_predictions = []
            all_actuals = []
            
            with torch.no_grad():
                for batch_X, batch_y in test_loader:
                    batch_X = batch_X.to(device)
                    predictions = model(batch_X, teacher_forcing_ratio=0.0)
                    all_predictions.append(predictions.cpu().numpy())
                    all_actuals.append(batch_y.numpy())
                    
            all_predictions = np.concatenate(all_predictions, axis=0)
            all_actuals = np.concatenate(all_actuals, axis=0)
            
            # Inverse transform sequence and slice to 1st step (1-hour ahead) for standard comparison
            N, H, F = all_predictions.shape
            inv_predictions_all = scaler.inverse_transform(all_predictions.reshape(-1, F)).reshape(N, H, F)
            inv_actuals_all = scaler.inverse_transform(all_actuals.reshape(-1, F)).reshape(N, H, F)
            
            inv_predictions = inv_predictions_all[:, 0, :]
            inv_actuals = inv_actuals_all[:, 0, :]
            
        else: # lstm or gru
            test_dataset = WaterQualityDataset(X_test_1, y_test_1)
            test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
            
            all_predictions = []
            all_actuals = []
            
            with torch.no_grad():
                for batch_X, batch_y in test_loader:
                    batch_X = batch_X.to(device)
                    predictions = model(batch_X)
                    all_predictions.append(predictions.cpu().numpy())
                    all_actuals.append(batch_y.numpy())
                    
            all_predictions = np.concatenate(all_predictions, axis=0)
            all_actuals = np.concatenate(all_actuals, axis=0)
            
            inv_predictions = scaler.inverse_transform(all_predictions)
            inv_actuals = scaler.inverse_transform(all_actuals)
            
        # Calculate metrics for each feature
        features = ['water_pH', 'TDS', 'water_temp']
        metrics = {}
        for idx, feat in enumerate(features):
            y_act = inv_actuals[:, idx]
            y_pred = inv_predictions[:, idx]
            
            mse = mean_squared_error(y_act, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_act, y_pred)
            r2 = r2_score(y_act, y_pred)
            
            metrics[feat] = {'RMSE': rmse, 'MAE': mae, 'R2': r2 * 100} # percentage R2
            
        results[name] = metrics
        print(f"Evaluation for {name.upper()} complete.")
        
    if not results:
        print("Error: No models were evaluated.")
        return
        
    # Generate Markdown Table Report
    report = "# 📊 Báo Cáo So Sánh Hiệu Năng Các Mô Hình\n\n"
    report += "Báo cáo này tự động đánh giá và so sánh sai số dự báo **1 giờ tiếp theo (1-Hour Ahead)** của các mô hình trên tập kiểm thử chung.\n\n"
    
    features = ['water_pH', 'TDS', 'water_temp']
    units = ['', ' ppm', ' °C']
    
    for idx, feat in enumerate(features):
        report += f"### 📌 Chỉ số: {feat} ({units[idx].strip() if units[idx] else 'không đơn vị'})\n\n"
        report += "| Mô hình | RMSE ↓ | MAE ↓ | R² Score (%) ↑ |\n"
        report += "| :--- | :---: | :---: | :---: |\n"
        
        # Sort models by R² score descending
        sorted_models = sorted(results.keys(), key=lambda x: results[x][feat]['R2'], reverse=True)
        
        for name in sorted_models:
            rmse_val = results[name][feat]['RMSE']
            mae_val = results[name][feat]['MAE']
            r2_val = results[name][feat]['R2']
            
            report += f"| **{name.upper()}** | {rmse_val:.4f}{units[idx]} | {mae_val:.4f}{units[idx]} | {r2_val:.2f}% |\n"
        report += "\n---\n\n"
        
    print("\n=== COMPARISON REPORT ===")
    print(report)
    
    # Save report
    os.makedirs("../artifacts", exist_ok=True)
    with open("../artifacts/model_comparison.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Report saved successfully to artifacts/model_comparison.md")

if __name__ == "__main__":
    evaluate_models()
