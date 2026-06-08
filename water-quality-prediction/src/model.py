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

class WaterQualityGRU(nn.Module):
    def __init__(self, input_size=3, hidden_size=64, num_layers=2, output_size=3, dropout=0.2):
        """
        GRU Model for Water Quality time series forecasting.
        - input_size: number of features (3)
        - hidden_size: number of hidden units in GRU cell
        - num_layers: number of stacked GRU layers
        - output_size: number of features to predict (3)
        - dropout: dropout probability to prevent overfitting
        """
        super(WaterQualityGRU, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_size)
        )
        
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_size)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.gru(x, h0)
        out_last = out[:, -1, :]
        prediction = self.fc(out_last)
        return prediction

class WaterQualitySeq2Seq(nn.Module):
    def __init__(self, input_size=3, hidden_size=64, num_layers=2, output_size=3, forecast_horizon=12, dropout=0.2):
        """
        Sequence-to-Sequence (Encoder-Decoder) LSTM Model for direct multi-step forecasting.
        - input_size: number of features (3)
        - hidden_size: number of hidden units in Encoder LSTM and Decoder LSTMCell
        - num_layers: number of stacked LSTM layers in Encoder
        - output_size: number of features to predict (3)
        - forecast_horizon: number of future time steps to forecast directly (12)
        - dropout: dropout probability
        """
        super(WaterQualitySeq2Seq, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.forecast_horizon = forecast_horizon
        self.output_size = output_size
        
        # Encoder: Stacked LSTM
        self.encoder = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        
        # Decoder cell: LSTMCell processes step-by-step
        self.decoder_cell = nn.LSTMCell(
            input_size=input_size,
            hidden_size=hidden_size
        )
        
        # Regression head for each prediction step
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x, teacher_forcing_ratio=0.0, target_y=None):
        # x: (batch_size, seq_len, input_size)
        # target_y: (batch_size, forecast_horizon, input_size) - only used if training with teacher forcing
        batch_size = x.size(0)
        
        # Encode sequence
        _, (h, c) = self.encoder(x)
        
        # LSTMCell expects shape (batch_size, hidden_size)
        # We take the hidden state and cell state of the top layer (last index of the stacked LSTM)
        dec_h = h[-1]
        dec_c = c[-1]
        
        # First decoder input is the last step of the input sequence
        dec_input = x[:, -1, :]
        
        outputs = []
        for t in range(self.forecast_horizon):
            dec_h, dec_c = self.decoder_cell(dec_input, (dec_h, dec_c))
            pred = self.fc(dec_h) # (batch_size, output_size)
            outputs.append(pred.unsqueeze(1)) # (batch_size, 1, output_size)
            
            # Next input selection
            import random
            if target_y is not None and random.random() < teacher_forcing_ratio:
                dec_input = target_y[:, t, :]
            else:
                dec_input = pred # Autoregressive feedback loop
                
        return torch.cat(outputs, dim=1) # (batch_size, forecast_horizon, output_size)

if __name__ == "__main__":
    dummy_input = torch.randn(8, 24, 3) # Batch of 8, lookback of 24, 3 features
    print(f"Dummy Input shape: {dummy_input.shape}\n")
    
    # 1. Test LSTM
    lstm_model = WaterQualityLSTM()
    lstm_output = lstm_model(dummy_input)
    print(f"LSTM Output shape: {lstm_output.shape}")
    
    # 2. Test GRU
    gru_model = WaterQualityGRU()
    gru_output = gru_model(dummy_input)
    print(f"GRU Output shape: {gru_output.shape}")
    
    # 3. Test Seq2Seq
    seq2seq_model = WaterQualitySeq2Seq()
    seq2seq_output = seq2seq_model(dummy_input)
    print(f"Seq2Seq Output shape (default horizon=12): {seq2seq_output.shape}")

