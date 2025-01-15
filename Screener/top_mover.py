import numpy as np
import pandas as pd
import yfinance as yf


# Custom
from TechnicalAnalysis.ta import TechnicalAnalysis


class TopMovers:
    def __init__(
        self,
        is_crypto: bool = False,
        crypto_quotes: str = "USD",
        convert_tz: bool = True,
        local_tz: str = "PST",
    ) -> None:
        self.is_crypto = is_crypto
        self.crypto_quotes = crypto_quotes
        self.convert_tz = convert_tz
        self.local_tz = local_tz.upper()
        self.tickers = []
        self.data = pd.DataFrame()

    def set_data(
        self,
        tickers: list,
        multi_fetch: bool = False,
        merge_data: bool = False,
        candle_period: str = "1d",
        candle_interval: str = "5m",
        candle_prepost: bool = True,
    ):
        if self.is_crypto:
            tickers = [f"{t}-{self.crypto_quotes}" for t in tickers]
        self.tickers = tickers

        if multi_fetch:
            data = self._multi_fetch_candle(
                tickers,
                interval=candle_interval,
                period=candle_period,
                prepost=candle_prepost,
            )
            data = self._apply_volume(data, multi_fetched=multi_fetch)
            data = self._apply_technical_indicators(data, multi_fetched=multi_fetch)

        else:

            data = {}
            for t in self.tickers:
                print(f"T: {t}")
                candle = self._fetch_candle(t)
                candle = self._apply_volume(candle)
                candle = self._apply_technical_indicators(candle)
                data[t] = candle
                if merge_data:
                    data = self._merge_dataframes(data)
        self.data = data

    def get_data(self):
        return self.data

    def _multi_fetch_candle(
        self,
        tickers: list,
        interval: str = "5m",
        period: str = "1d",
        prepost: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch Open, High, Low, Close, Volume (OHLCV) data from Yahoo Finance.

        Parameters
        ----------
        ticker : list
            List of tickers to retrieve data for.
        interval : str, optional
            Interval of the candles, by default "5m"
        period : str, optional
            Time period of the candles, by default "1d"
        prepost : bool, optional
            Determines if pre-market/post-market data is included, by default True

        Returns
        -------
        pd.DataFrame
            Multi-columned dataframe containing OHLCV data.
        """

        candle = yf.download(tickers, period=period, interval=interval, prepost=prepost)
        if self.convert_tz:
            tz = self._get_tz()
            candle.index = candle.index.tz_convert(tz)
        return candle

    def _fetch_candle(
        self,
        ticker: str,
        interval: str = "5m",
        period: str = "1d",
        prepost: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch Open, High, Low, Close, Volume (OHLCV) data from Yahoo Finance.

        Parameters
        ----------
        ticker : str
            Ticker to retrieve data for.
        interval : str, optional
            Interval of the candles, by default "5m"
        period : str, optional
            Time period of the candles, by default "1d"
        prepost : bool, optional
            Determines if pre-market/post-market data is included, by default True

        Returns
        -------
        pd.DataFrame
            Returns OHLCV data.
        """

        if self.is_crypto:
            candle = yf.download(ticker, period=period, interval=interval)
        else:
            candle = yf.download(
                ticker,
                period=period,
                interval=interval,
                prepost=prepost,
            )
        candle.columns = candle.columns.droplevel(1)
        if self.convert_tz:
            tz = self._get_tz()
            candle.index = candle.index.tz_convert(tz)
        return candle

    def _get_tz(self):
        if self.local_tz == "PST":
            return "America/Los_Angeles"

    """
    ===================================================
    Data Manipulation
    ===================================================
    """

    def _merge_dataframes(self, data: dict):
        """
        Merge multiple dataframes into a single dataframe.
        Source dataframes are stored in a 'dict'.

        data: dict
            Dictionary with tickers as keys. Each key has an associated dataframe of candles.

        return: pd.DataFrame
            Merged Dataframes.
        """
        print(f"DATA: {data}  TYPE: {type(data)}")
        tickers = list(data.keys())
        values = list(data.values())

        df = pd.concat(values, axis=1, keys=tickers)
        return df

    """
    ===================================================
    Indicators
    ===================================================
    """

    def _apply_volume(
        self, df: pd.DataFrame, window: int = 15, multi_fetched: bool = False
    ):
        """
        Apply volume data to dataframe. Will calculate the average volume within the last 'window' days.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe containing OHLCV candle data.
        window : int, optional
            Window to use for the average volume calculation, by default 15
        multi_fetched : bool, optional
            _description_, by default False

        Returns
        -------
        pd.DataFrame
            _description_
        """
        if multi_fetched:
            for t in self.tickers:
                df[("Average_Volume", t)] = (
                    df[("Volume", t)].rolling(window=window).mean()
                )
            for t in self.tickers:
                df[("Relative_Volume", t)] = (
                    df[("Volume", t)] / df[("Average_Volume", t)]
                )
        else:
            df["Average_Volume"] = df["Volume"].rolling(window=window).mean()
            df["Relative_Volume"] = df["Volume"] / df["Average_Volume"]
        return df

    def _apply_technical_indicators(
        self,
        df: pd.DataFrame,
        rsi_window: int = 14,
        emas: list = [9, 20, 200],
        multi_fetched: bool = False,
    ):
        """
        Apply RSI and EMA indicators to dataframe.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe containing OHLCV candle data.
        rsi_window : int, optional
            Window to use for RSI indicator, by default 14
        emas : list, optional
            Window to use for EMA indicator, by default [9, 20, 200]
        multi_fetched : bool, optional
            Determines if the structure of the dataframe is multi-columned, or single, by default False

        Returns
        -------
        pd.DataFrame
            Return the dataframe with indicators columns applied.
        """

        ta = TechnicalAnalysis()
        if multi_fetched:

            for t in self.tickers:
                # RSI
                df[("RSI", t)] = ta.rsi(df[("Close", t)].dropna(), window=rsi_window)
            for e in emas:
                # EMA
                for e in emas:
                    for t in self.tickers:
                        df[(f"EMA_{e}", t)] = ta.ema(df[("Close", t)], window=e)
        else:
            # RSI
            df["RSI"] = ta.rsi(df["Close"], window=rsi_window)
            # EMA
            for e in emas:
                df[f"ema_{e}"] = ta.ema(df["Close"], e)
        return df
