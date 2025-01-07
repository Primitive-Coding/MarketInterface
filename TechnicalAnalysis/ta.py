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
