import numpy as np
import pandas as pd
import yfinance as yf


class PairTrade:
    def __init__(self, base_ticker: str, compare_ticker: str) -> None:
        self.base_ticker = base_ticker.upper()
        self.compare_ticker = compare_ticker.upper()

    def set_data(self, interval: str = "1m", period: str = "max"):
        # Base data
        base_candle = yf.download(
            self.base_ticker, interval=interval, period=period, multi_level_index=False
        )
        base_dates = base_candle.index.to_list()
        recent_base_date = base_dates[-1]
        # Compare data
        compare_candle = yf.download(
            self.compare_ticker,
            interval=interval,
            period=period,
            multi_level_index=False,
        )
        last_price = compare_candle["Close"].iloc[-1]
        compare_dates = compare_candle.index.to_list()
        compare_start = compare_dates[0]
        compare_end = compare_dates[-1]
        # Base anchor and end
        ba = base_candle.loc[compare_start, "Close"]
        be = base_candle.loc[compare_end, "Close"]
        b_change = (be - ba) / ba
        b_current_start = base_candle.loc[compare_end, "Close"]
        b_current_end = base_candle.loc[recent_base_date, "Close"]
        b_current_change = (b_current_end - b_current_start) / b_current_start
        # Compare anchor and end
        ca = compare_candle.loc[compare_start, "Close"]
        ce = compare_candle.loc[compare_end, "Close"]
        c_change = (ce - ca) / ca
        compare_multiplier = c_change / b_change
        print(f"C: {c_change}  B: {b_change}")
        print(f"COmpare: {compare_multiplier}")
        expected_compare_change = b_current_change * compare_multiplier

        expected_price = (last_price * expected_compare_change) + last_price
        print(
            f"[Previous]:\n\nBitcoin: {b_change}\nMSTR: {c_change}\n\n\n[Next]:\n\nBitcoin: {b_current_change}  MSTR: {expected_compare_change}"
        )

        print(f"EXPECTED: {expected_price}")
