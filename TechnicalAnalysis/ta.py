import warnings
import pandas as pd
import pandas_ta as pta


class TechnicalAnalysis:
    def __init__(self):
        pass

    def rsi(self, close_values: pd.Series, window: int = 14) -> pd.Series:
        rsi = pta.rsi(close=close_values, length=window)
        return rsi

    def ema(self, close_values: pd.Series, window: int) -> pd.Series:
        ema = pta.ema(close=close_values, length=window)
        return ema

    def vwap(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume_share_qty: pd.Series,
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            vwap = pta.vwap(high=high, low=low, close=close, volume=volume_share_qty)
        return vwap
