import os
import time
import numpy as np
import pandas as pd
import datetime as dt

# Custom
from Crypto.CEX.cex import CentralizedExchange

# Technical Analysis
from TechnicalAnalysis.ta import TechnicalAnalysis

# PyTorch
import torch
import torch.nn as nn
import torch.optim as optim

"""
==================================================================================================================================
Datasets
==================================================================================================================================
"""


class Dataset:
    def __init__(
        self,
        ticker: str,
        data_source: str = "coinbase",
        features: list = [
            "close",
            "volume",
            "rsi",
            "ema_9",
            "ema_20",
            "ema_200",
            "average_volume",
            # "relative_volume",
        ],
    ) -> None:
        self.ticker = ticker.upper()
        self.data_source = data_source.lower()
        self.features = features
        self.data = pd.DataFrame()

    def set_data(self, apply_features: bool = True):
        """
        Set data from Centralized Exchange of choice in the 'self.data' variable.

        Parameters
        ----------
        apply_features : bool, optional
            Determines if technical analysis is applied, by default True
        """
        cex = CentralizedExchange(self.data_source)
        candles = cex.fetch_candles(self.ticker, apply_indicators=apply_features)
        self.data = candles

    def get_data(self):
        """
        Get the data set in 'set_data()'.
        Will check if empty to avoid multiple queries.

        Returns
        -------
        pd.DataFrame
            Dataframe containing OHLCV, and any features.
        """
        if self.data.empty:
            self.set_data()
        return self.data

    def create_features(self, trailing_len: int = 5):
        """
        Create the input feature for the neural network.

        Parameters
        ----------
        trailing_len : int, optional
            Determines how many historical candles will be included for each feature, by default 5

        Returns
        -------
        pd.DataFrame
            Dataframe containing features, and their trailing values (t, t-1, t-2, etc.)
        """
        candles = self.get_data()
        candles = candles[self.features]
        feature_df = pd.DataFrame()

        OVERBOUGHT = 70
        OVERSOLD = 30

        feature_df["rsi_overbought"] = candles["rsi"] > OVERBOUGHT
        feature_df["rsi_oversold"] = candles["rsi"] < OVERSOLD
        feature_df["rsi_neutral"] = (candles["rsi"] < OVERBOUGHT) & (
            candles["rsi"] > OVERSOLD
        )
        feature_df["close_over_short"] = candles["close"] > candles["ema_9"]
        feature_df["close_over_medium"] = candles["close"] > candles["ema_20"]
        feature_df["close_over_long"] = candles["close"] > candles["ema_200"]
        feature_df["volume_over_average"] = (
            candles["volume"] > candles["average_volume"]
        )
        cols = feature_df.columns.to_list()
        for c in cols:
            for t in range(1, trailing_len + 1):
                feature_df[f"{c}_t-{t}"] = feature_df[c].shift(t)
        return feature_df

    def create_targets(self):
        """
        Targets for the neural network. NaN values are kept to keep array sizing the same as the features. But eventually they are removed.

        Returns
        -------
        list
            List of target values. Includes NaN values.
        """
        candles = self.get_data()
        targets = []
        for i, row in candles.iterrows():
            change = row["change"]
            # if pd.isna(change):
            #     pass
            # else:
            if change > 0:  #  UP = 0
                targets.append(0)
            else:  # DOWN = 1
                targets.append(1)
        return targets

    def get_dataset(self) -> pd.DataFrame:
        """
        Unify the features and targets into a single dataframe.

        Returns
        -------
        pd.DataFrame
            Dataframe containing features and targets.
        """
        features = self.create_features()
        targets = self.create_targets()
        features["target"] = targets
        features.dropna(inplace=True)
        return features


"""
==================================================================================================================================
Neural Network
==================================================================================================================================
"""


class Network(nn.Module):
    def __init__(self, input_dim: int):
        super(Network, self).__init__()
        # Input layer: 42 features
        self.fc1 = nn.Linear(input_dim, 64)  # 42 -> 64 neurons
        self.fc2 = nn.Linear(64, 128)  # 64 -> 128 neurons
        self.fc3 = nn.Linear(128, 64)  # 128 -> 64 neurons
        self.output = nn.Linear(64, 1)  # 64 -> 1 neuron (binary output)

        # Activation function
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.relu(self.fc1(x))  # Input -> Hidden Layer 1
        x = self.relu(self.fc2(x))  # Hidden Layer 1 -> Hidden Layer 2
        x = self.relu(self.fc3(x))  # Hidden Layer 2 -> Hidden Layer 3
        x = self.sigmoid(self.output(x))  # Hidden Layer 3 -> Output Layer
        return x


"""
==================================================================================================================================
Interface
==================================================================================================================================
"""


def prepare_data():
    dataset = Dataset("BTC")

    features = dataset.get_dataset()
    target = features["target"]
    features.drop("target", axis=1, inplace=True)
    array = features.to_numpy()
    array = array.astype(bool)
    # Convert to tensor.
    features = torch.tensor(array, dtype=torch.bool)
    target = torch.tensor(target, dtype=torch.float32)
    print(f"Features: {target}   SHape: {features.shape[1]}")
    input_dim = features.shape[1]
    train_model(features, target)


def train_model(
    features_tensor,
    target_tensor,
    epochs: int = 1000,
    model_name: str = "trailing_candles",
):
    input_dim = features_tensor.shape[1]

    path_to_model = f"./MachineLearning/NN/Storage/{model_name}.pth"
    model = Network(input_dim)
    try:
        model.load_state_dict(torch.load(path_to_model))
    except Exception as e:
        print(f"E: {e}")

    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Example training loop
    for epoch in range(epochs + 1):  # Number of epochs
        optimizer.zero_grad()  # Reset gradients

        # Forward pass
        predictions = model(features_tensor.float())  # Ensure input is float

        # Calculate loss
        loss = criterion(predictions.squeeze(), target_tensor.float())

        # Backward pass and optimization
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch + 1}/{epochs}], Loss: {loss.item():.4f}")

    torch.save(model.state_dict(), path_to_model)
