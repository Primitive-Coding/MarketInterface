import numpy as np
import pandas as pd


# Centralized Exchange
from Crypto.CEX.cex import CentralizedExchange
from Crypto.CEX.cex_aggregator import CexAggregator

# Lists of tickers
from LocalStorage.ticker_lists import gmx

# Plotting
import mplfinance as mpf


class LeverageScanner:
    def __init__(self, tickers: list = [], cex: str = "coinbase") -> None:
        if tickers == []:
            self.tickers = []
        else:
            self.tickers = tickers
        self.cex = cex
        self.data = {}

    def set_ticker_data(self, tickers: list = []):
        if tickers == []:
            tickers = self.tickers
        for t in tickers:
            cex = CentralizedExchange(self.cex)
            d = cex.fetch_candles(t)
            self.data[t] = d

    def plot(self, tickers: list = []):
        if self.data == {}:
            self.set_ticker_data(tickers)
        add_plots = []
        index = 0
        base_df = pd.DataFrame()
        panel = 0
        for k, v in self.data.items():
            if index == 0:
                base_df = v
                add_plots.append(mpf.make_addplot(base_df["ema_9"], panel=0))
                add_plots.append(mpf.make_addplot(base_df["ema_20"], panel=0))
                add_plots.append(mpf.make_addplot(base_df["ema_200"], panel=0))
            else:
                df = v
                add_plots.append(mpf.make_addplot(df["ema_9"], panel=panel))
                add_plots.append(mpf.make_addplot(df["ema_20"], panel=panel))
                add_plots.append(mpf.make_addplot(df["ema_200"], panel=panel))
            panel += 1
            index += 1

        mpf.plot(
            base_df,
            type="candle",
            addplot=add_plots,
            volume=False,
            panel_ratios=(3, 1),
            figsize=(10, 8),
        )
