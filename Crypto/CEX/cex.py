import asyncio
import numpy as np
import pandas as pd

from TechnicalAnalysis.ta import TechnicalAnalysis

# CCXT
import ccxt
import ccxt.async_support as ccxt_async
from ccxt.base.errors import BadSymbol, NotSupported

import mplfinance as mpf

import datetime as dt


free_exchanges = ["hyperliquid", "paradex", "vertex"]


class CentralizedExchange:
    def __init__(self, name):
        self.name = name
        self.exchange = getattr(ccxt, name)()
        self.stable_coins = ["USD", "USDC", "USDT", "DAI"]
        self.ta = TechnicalAnalysis()

        self.technical_indicators = {
            "rsi": {"oversold": 30, "overbought": 70},
            "ema": {"fast": 9, "mid": 20, "slow": 200},
        }

    def get_exchanges_with_free_ohlcv(self):
        # Get all supported exchanges
        exchanges = ccxt.exchanges
        supported_exchanges = []

        for exchange_id in exchanges:
            try:
                # Initialize the exchange
                exchange = getattr(ccxt, exchange_id)()
                # Check if it supports OHLCV
                if exchange.has.get("fetchOHLCV", False):
                    # Check if API key is required
                    if not exchange.requiredCredentials["apiKey"]:
                        supported_exchanges.append(exchange_id)
            except Exception as e:
                print(f"Error checking {exchange_id}: {e}")

        return supported_exchanges

    def compare_candles(self, base_ticker: str, compare_ticker: str):
        b_candle = self.fetch_candles(base_ticker)
        c_candle = self.fetch_candles(compare_ticker)
        b_recv = False
        c_recv = False
        try:
            b_candle = b_candle["change"].dropna().to_list()
            b_recv = True
        except KeyError:
            pass
        try:
            c_candle = c_candle["change"].dropna().to_list()
            c_recv = True
        except KeyError:
            pass

        if b_recv and c_recv:
            similarity_scores = [
                1 - abs(b - c) / max(b_candle) for b, c in zip(b_candle, c_candle)
            ]
            return similarity_scores
        else:
            return np.nan

    async def async_fetch_candles(
        self, ticker: str, market: str = "USD", timeframe: str = "1m", limit: int = 300
    ):
        symbol = f"{ticker}/{market}"
        exchange = getattr(ccxt_async, self.name)()
        candles = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return candles

    async def async_fetch_multiple_candles(
        self, tickers: str, market: str = "USD", timeframe: str = "1m", limit: int = 300
    ):
        tasks = [
            self.async_fetch_candles(ticker, market, timeframe, limit)
            for ticker in tickers
        ]
        results = await asyncio.gather(*tasks)
        return results

    def fetch_candles(
        self,
        ticker: str,
        market: str = "USD",
        timeframe="1m",
        limit: int = 300,
        stable_coin: bool = True,
        apply_indicators: bool = True,
        indicators: list = ["rsi", "ema"],
    ):
        ohlcv = self._fetch_candle(
            ticker, timeframe, limit, stable_coin=stable_coin, market=market
        )

        # Convert to DataFrame
        df = pd.DataFrame(
            ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume_qty"]
        )

        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            pst_offset = dt.timedelta(hours=-8)
            df["timestamp"] = df["timestamp"] + pst_offset
            df.set_index("timestamp", inplace=True)
            df["change"] = df["close"].pct_change() * 100
            df["volume"] = df["volume_qty"] * df["close"]
            df["average_volume"] = df["volume"].rolling(window=30).mean()
            df["relative_volume"] = df["volume"] / df["average_volume"]
            if apply_indicators:
                self._apply_indicators(df, indicators)
        return df

    def _fetch_candle(
        self, ticker: str, timeframe, limit, stable_coin: bool, market: str = ""
    ):
        index = 0
        num_stables = len(self.stable_coins)
        attempt_alt_delimeter = False
        while True:
            if stable_coin:
                market = self.stable_coins[index]

            if attempt_alt_delimeter:
                symbol = f"{ticker.upper()}-{market.upper()}"
            else:
                symbol = f"{ticker.upper()}/{market.upper()}"
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                return ohlcv
            except BadSymbol:
                index += 1
                if index == num_stables:
                    index = 0
                    if attempt_alt_delimeter:
                        return pd.DataFrame()
                    attempt_alt_delimeter = True
            except NotSupported:
                print(f"Ticker: {ticker}")

    def _apply_indicators(self, df: pd.DataFrame, indicators: list):

        if "rsi" in indicators:
            df["rsi"] = self.ta.rsi(df["close"])
        if "ema" in indicators:
            for k, v in self.technical_indicators["ema"].items():
                key = f"ema_{v}"
                skey = f"spread_{v}"
                okey = f"ema_{v}_over"
                df[key] = self.ta.ema(df["close"], v)
                df[skey] = ((df[key]) - df["close"]) / abs(df["close"]) * 100
                df[okey] = df["close"] > df[key]

        if "vwap" in indicators:
            df["vwap"] = self.ta.vwap(
                df["high"],
                low=df["low"],
                close=df["close"],
                volume_share_qty=df["volume_qty"],
            )
            df["vwap_spread"] = ((df["vwap"] - df["close"]) / abs(df["close"])) * 100

        return df

    def aggregate_candles(
        self,
        tickers: list,
        market: str = "USD",
        timeframe="1m",
        limit: int = 300,
        stable_coin: bool = True,
        add_info=["rsi", "spread_9", "spread_20", "spread_200", "relative_volume"],
    ):

        data = {}
        for t in tickers:
            candles = self.fetch_candles(t, market, timeframe, limit, stable_coin)
            print(f"Candles: {candles}")
            data[(t, "open")] = candles["open"]
            data[(t, "high")] = candles["high"]
            data[(t, "low")] = candles["low"]
            data[(t, "close")] = candles["close"]
            data[(t, "volume")] = candles["volume"]

            if add_info != []:
                for ai in add_info:
                    try:
                        data[(t, ai)] = candles[ai]
                        data[(t, f"traj_{ai}")] = self._get_trajectory(
                            values=candles[ai], window=5
                        )
                    except KeyError:
                        pass
        data = pd.DataFrame(data)

        vals = self._find_highest(data, "traj_rsi")
        print(f"DATA: {vals}")

    """
    ==================================================================================================================================
    Markets
    ==================================================================================================================================
    """

    def fetch_markets(self):
        markets = self.exchange.fetch_markets()
        data = {
            "base": [],
            "quote": [],
            "symbol": [],
            "price": [],
            "exchange_name": [],
        }
        price_keys = ["price", "oraclePx"]
        for l in markets:
            # if self.name == "coinbase":
            #     print(f"L: {l}")
            #     exit()
            # print(f"KEYS: {l.keys()}")
            data["base"].append(l["base"])
            data["quote"].append(l["quote"])
            symbol = l["symbol"]
            if ":" in symbol:
                symbol = symbol.split(":")[0]
            data["symbol"].append(symbol)
            price = self.match_keys(l["info"], price_keys)
            data["price"].append(price)
            data["exchange_name"].append(self.name)
        markets = pd.DataFrame(data)
        return markets

    def match_keys(self, info: dict, keys_to_match: list):
        index = 0
        while True:
            try:
                key = keys_to_match[index]
            except IndexError:
                return np.nan
            try:
                val = info[key]
                return val
            except KeyError:
                pass
            index += 1

    """
    ==================================================================================================================================
    Plots
    ==================================================================================================================================
    """

    def plot(self, ticker: str):
        add_plots = []
        candles = self.fetch_candles(ticker)
        print(f"Candles: {candles}")

        ohlcv = candles[["open", "high", "low", "close", "volume"]]
        colors = ["red", "orange", "yellow"]
        index = 0
        for k, v in self.technical_indicators["ema"].items():
            key = f"ema_{v}"
            color = colors[index]
            add_plots.append(mpf.make_addplot(candles[key], color=color, label=key))
            index += 1

        mpf.plot(
            ohlcv,
            type="candle",  # Candlestick plot
            style="charles",  # Choose a style (e.g., 'charles', 'yahoo', 'default')
            addplot=add_plots,
            title=f"{ticker} Candles",
            volume=True,
            ylabel="Price",
            ylabel_lower="Volume",
            figratio=(10, 6),  # Aspect ratio of the figure
            figscale=1.2,
        )

    """
    ==================================================================================================================================
    Utilities
    ==================================================================================================================================
    """

    def _get_trajectory(self, values: pd.Series, window: int):
        t = values.shift(window)
        v = (values - t) / t
        return v

    def _find_highest(self, df: pd.DataFrame, column: str):
        cols = df.columns.to_list()
        tickers = [c[0] for c in cols]
        tickers = list(set(tickers))  # Remove duplicates.
        data = {}
        for t in tickers:
            value = df[t][column].iloc[-1]
            data[t] = value
        # Find largest key and value.
        largest_key = max(data, key=data.get)
        largest_value = data[largest_key]
        return largest_key, largest_value

    def _find_trend_length(self, values: pd.Series):
        pass
