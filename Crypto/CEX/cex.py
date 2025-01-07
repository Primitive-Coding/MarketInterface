import numpy as np
import pandas as pd

from TechnicalAnalysis.ta import TechnicalAnalysis

# CCXT
import ccxt
from ccxt.base.errors import BadSymbol

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

    def fetch_candles(
        self,
        ticker: str,
        market: str = "USD",
        timeframe="1m",
        limit: int = 300,
        stable_coin: bool = True,
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
            df["volume"] = df["volume_qty"] * df["close"]
            for k, v in self.technical_indicators["ema"].items():
                key = f"ema_{v}"
                skey = f"spread_{v}"
                df[key] = self.ta.ema(df["close"], v)
                df[skey] = ((df[key]) - df["close"]) / abs(df["close"]) * 100

            df["rsi"] = self.ta.rsi(df["close"])

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
