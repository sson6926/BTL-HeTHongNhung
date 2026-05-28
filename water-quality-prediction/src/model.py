import torch
import torch.nn as nn

class WaterQualityLSTM(nn.Module):
    def __init__(self, input_size=3, hidden_size=64, num_layers=2, output_size=3, dropout=0.2):
        """
        LSTM Model for Water Quality time series forecasting.
        - input_size: number of features (3: water_pH, TDS, water_temp)
        - hidden_size: number of hidden units in LSTM cell
        - num_layers: number of stacked LSTM layers
        - output_size: number of features to predict (3)
        - dropout: dropout probability to prevent overfitting
        """
        super(WaterQualityLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM Layer
        # batch_first=True means the input/output tensors are of shape (batch, seq, feature)
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        
        # Fully connected layers to output predictions
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_size)
        )
        
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_size)
        
        # Initialize hidden state (h0) and cell state (c0) with zeros
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # Pass through LSTM
        # out shape: (batch_size, seq_len, hidden_size)
        out, _ = self.lstm(x, (h0, c0))
        
        # Get the output from the last time step
        # out shape: (batch_size, hidden_size)
        out_last = out[:, -1, :]
        
        # Pass through the regression head
        # prediction shape: (batch_size, output_size)
        prediction = self.fc(out_last)
        
        return prediction

if __name__ == "__main__":
    # Test model with dummy input
    model = WaterQualityLSTM()
    dummy_input = torch.randn(8, 24, 3) # Batch of 8, lookback of 24, 3 features
    dummy_output = model(dummy_input)
    print(f"Dummy Input shape: {dummy_input.shape}")
    print(f"Dummy Output shape: {dummy_output.shape}")
    print(dummy_output)
