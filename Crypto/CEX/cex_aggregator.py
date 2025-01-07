import numpy as np
import pandas as pd
from Crypto.CEX.cex import CentralizedExchange

import datetime as dt


class CexAggregator:
    def __init__(self, cex_list: list):
        self.exchanges = cex_list
        self.cex_objects = {c: CentralizedExchange(c) for c in cex_list}

    def get_last_price(self, ticker: str, market: str = "USD"):
        markets = pd.DataFrame()
        for k, v in self.cex_objects.items():
            cex_market = v.fetch_markets()
            markets = pd.concat([markets, cex_market], axis=0)
            # candles = v.get_OHLCV(ticker, market)
            # print(f"Candles: {candles}")
        print(f"Markets: {markets}")

    def get_candles(self, ticker: str, market: str = "USD"):
        """
        Get the candles from every exchange in 'self.exchanges' for the specified pair.

        Parameters
        ----------
        ticker : str
            Ticker of the asset.
        market : str, optional
            Asset to quote the 'ticker' in, by default "USD"

        Returns
        -------
        pd.DataFrame
            DataFrame containing candle data.
        """
        candles = {}
        for k, v in self.cex_objects.items():
            candle = v.fetch_candles(ticker, market=market)
            print(f"Candle: {candle}")
            candles[k] = candle
        return candles

    def aggregate_candles(self, tickers: list, market: str = "USD"):
        candles = {}
        for t in tickers:
            candles[t] = self.get_candles(t, market)

        self._aggregate_columns(candles, ["close", "rsi", "spread_200"])
        return candles

    def _aggregate_columns(self, candles: dict, column: str):
        """


        Parameters
        ----------
        candles : dict
            Candles from 'aggregate_candles()'.
        """
        data = {}

        if type(column) == str:
            column = [column]

        for k, v in candles.items():
            for col in column:
                for cex in self.exchanges:
                    df = candles[k][cex]
                    if not df.empty:
                        values = df[col]
                        if not values.empty:
                            data[(k, col)] = values

        data = pd.DataFrame(data)

        print(f"Data: {data}")
