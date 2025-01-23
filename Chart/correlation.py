# Data
import numpy as np
import pandas as pd
import yfinance as yf

# Plotting
import seaborn as sns
import matplotlib.pyplot as plt


class Correlation:
    def __init__(self) -> None:
        pass

    def create_matrix(self, tickers: list):
        data = yf.download(tickers)
        close_prices = data["Close"]
        matrix = close_prices.corr()
        return matrix

    def plot_matrix(self, tickers: list):
        matrix = self.create_matrix(tickers)
        plt.figure(figsize=(10, 8))  # Set the figure size
        sns.heatmap(
            matrix,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            square=True,
            cbar_kws={"shrink": 0.8},
        )
        plt.title("Correlation Matrix")
        plt.show()
