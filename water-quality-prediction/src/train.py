import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from preprocess import preprocess_and_resample, prepare_lstm_data
from model import WaterQualityLSTM

# Set plotting style for professional look
sns.set_theme(style="darkgrid")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']

# Custom PyTorch Dataset for Time Series sequences
class WaterQualityDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

def train_model(epochs=100, batch_size=32, lr=0.001, patience=15):
    # Create artifacts directory if it doesn't exist
    os.makedirs("artifacts", exist_ok=True)
    
    # 1. Preprocess and prepare data
    df_resampled = preprocess_and_resample()
    X_train, y_train, X_test, y_test, scaler = prepare_lstm_data(df_resampled)
    
    # Save the scaler so we can reuse it during prediction
    with open("artifacts/scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    print("MinMaxScaler saved to artifacts/scaler.pkl")
    
    # Create PyTorch datasets and loaders
    train_dataset = WaterQualityDataset(X_train, y_train)
    test_dataset = WaterQualityDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # 2. Setup Device & Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")
    
    model = WaterQualityLSTM(input_size=3, hidden_size=64, num_layers=2, output_size=3, dropout=0.2)
    model = model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    
    # 3. Training Loop with Early Stopping
    train_losses = []
    test_losses = []
    
    best_loss = float('inf')
    patience_counter = 0
    best_model_weights = None
    
    print("\n--- Training LSTM Model ---")
    for epoch in range(1, epochs + 1):
        model.train()
        epoch_train_losses = []
        
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            # Forward pass
            predictions = model(batch_X)
            loss = criterion(predictions, batch_y)
            
            # Backward pass and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            epoch_train_losses.append(loss.item())
            
        # Evaluate on test set
        model.eval()
        epoch_test_losses = []
        
        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                predictions = model(batch_X)
                test_loss = criterion(predictions, batch_y)
                epoch_test_losses.append(test_loss.item())
                
        mean_train_loss = np.mean(epoch_train_losses)
        mean_test_loss = np.mean(epoch_test_losses)
        
        train_losses.append(mean_train_loss)
        test_losses.append(mean_test_loss)
        
        if epoch % 5 == 0 or epoch == 1:
            print(f"Epoch {epoch}/{epochs} | Train MSE Loss: {mean_train_loss:.6f} | Test MSE Loss: {mean_test_loss:.6f}")
            
        # Early stopping check
        if mean_test_loss < best_loss:
            best_loss = mean_test_loss
            patience_counter = 0
            best_model_weights = model.state_dict().copy()
            # Save the best model
            torch.save(best_model_weights, "artifacts/lstm_water_quality.pth")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\nEarly stopping triggered at epoch {epoch}! Best Test MSE Loss: {best_loss:.6f}")
                break
                
    # Load best weights back to the model
    if best_model_weights is not None:
        model.load_state_dict(best_model_weights)
        print("Loaded best weights from training phase.")
        
    # 4. Evaluation and Inversion of Scaling
    model.eval()
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
    
    # Inverse transform to original physical units
    # scaler expects shape (N, 3), and both arrays are (N, 3)
    inv_predictions = scaler.inverse_transform(all_predictions)
    inv_actuals = scaler.inverse_transform(all_actuals)
    
    features = ['water_pH', 'TDS', 'water_temp']
    units = ['', ' ppm', ' °C']
    
    print("\n--- Model Evaluation on Test Set ---")
    metrics_summary = {}
    for idx, feature in enumerate(features):
        y_act = inv_actuals[:, idx]
        y_pred = inv_predictions[:, idx]
        
        mse = mean_squared_error(y_act, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_act, y_pred)
        r2 = r2_score(y_act, y_pred)
        
        metrics_summary[feature] = {'RMSE': rmse, 'MAE': mae, 'R2': r2}
        print(f"\nMetrics for {feature}:")
        print(f"  - RMSE: {rmse:.4f}{units[idx]}")
        print(f"  - MAE:  {mae:.4f}{units[idx]}")
        print(f"  - R²:   {r2:.4f}")
        
    # 5. Visualizations
    # Plot 1: Loss Curve
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Train MSE Loss', color='#1f77b4', linewidth=2)
    plt.plot(test_losses, label='Test MSE Loss', color='#ff7f0e', linewidth=2)
    plt.title('LSTM Model Training History (MSE Loss)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Epochs', fontsize=12)
    plt.ylabel('Mean Squared Error (Scaled)', fontsize=12)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig("artifacts/lstm_loss_curve.png", dpi=150)
    plt.close()
    
    # Plot 2: actual vs predictions side-by-side
    fig, axes = plt.subplots(3, 1, figsize=(12, 15), sharex=False)
    colors = ['#1f77b4', '#2ca02c', '#d62728']
    
    # Let's plot only a subset of test set (e.g. 100 points) for visual clarity
    num_plot_points = min(150, len(inv_actuals))
    plot_indices = np.arange(num_plot_points)
    
    for idx, feature in enumerate(features):
        ax = axes[idx]
        ax.plot(plot_indices, inv_actuals[:num_plot_points, idx], label='Actual', color='#2b2b2b', alpha=0.6, linestyle='--', marker='o', markersize=4)
        ax.plot(plot_indices, inv_predictions[:num_plot_points, idx], label='LSTM Predicted', color=colors[idx], linewidth=2, marker='x', markersize=4)
        
        ax.set_title(f"Comparison of Actual vs Predicted: {feature}", fontsize=13, fontweight='bold')
        ax.set_ylabel(f"Value{units[idx]}", fontsize=11)
        ax.legend(fontsize=10, loc='upper right')
        
        # Display small box with error metrics
        metric_str = f"RMSE: {metrics_summary[feature]['RMSE']:.3f}\nMAE: {metrics_summary[feature]['MAE']:.3f}\nR²: {metrics_summary[feature]['R2']:.3f}"
        ax.text(0.02, 0.05, metric_str, transform=ax.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="#f7f7f7", ec="gray", alpha=0.8))
        
    plt.xlabel("Time Step (Hourly Test Samples)", fontsize=12)
    plt.suptitle("LSTM Multi-step predictions on Water Quality Test Set", fontsize=16, fontweight='bold', y=0.99)
    plt.tight_layout()
    plt.savefig("artifacts/lstm_predictions_vs_actuals.png", dpi=150)
    plt.close()
    
    print("\nVisualizations saved successfully:")
    print("  - artifacts/lstm_loss_curve.png")
    print("  - artifacts/lstm_predictions_vs_actuals.png")

if __name__ == "__main__":
    train_model()
