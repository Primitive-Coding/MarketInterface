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
            candles[k] = candle
        return candles

    def compare_candles(
        self, tickers: list, market: str = "USD", base_ticker: str = "BTC"
    ):
        data = {"ticker": [], "score": []}
        for k, v in self.cex_objects.items():
            for t in tickers:
                if t != base_ticker:
                    sim_score = v.compare_candles(base_ticker, compare_ticker=t)
                    try:
                        mean = sum(sim_score) / len(sim_score)
                    except TypeError:
                        mean = np.nan
                    data["ticker"].append(t)
                    data["score"].append(mean)
        df = pd.DataFrame(data).set_index("ticker")
        df.sort_values("score", inplace=True, ascending=False)
        return df

    def aggregate_candles(
        self,
        tickers: list,
        market: str = "USD",
        aggregate_columns: bool = False,
        columns_to_aggregate: list = ["close", "rsi", "vwap_spread", "spread_200"],
    ):
        candles = {}
        for t in tickers:
            candles[t] = self.get_candles(t, market)

        if aggregate_columns:
            candles = self._aggregate_columns(candles, columns_to_aggregate)
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
        return data

    def _find_max_value(self, aggregated_candles: pd.DataFrame, column: str):
        cols = aggregated_candles.columns.to_list()
        tickers = list(set([c[0] for c in cols]))
        data = {}
        for t in tickers:
            value = aggregated_candles[t][column].iloc[-1]
            data[t] = value
        max_key = max(data, key=data.get)
        max_value = data[max_key]
        return {max_key: max_value}

    def _find_min_value(self, aggregated_candles: pd.DataFrame, column: str):
        cols = aggregated_candles.columns.to_list()
        tickers = list(set([c[0] for c in cols]))
        data = {}
        for t in tickers:
            value = aggregated_candles[t][column].iloc[-1]
            data[t] = value
        max_key = min(data, key=data.get)
        max_value = data[max_key]
        return {max_key: max_value}
