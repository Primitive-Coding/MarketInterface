import re

# Data
import math
from scipy.stats import norm
from scipy.optimize import minimize
import numpy as np
import pandas as pd
import yfinance as yf


# Date & Time
import datetime as dt


class Options:
    def __init__(self, ticker: str, chain_date: str = "") -> None:
        self.ticker = ticker.upper()
        self.chain_date = chain_date
        self.obj = yf.Ticker(self.ticker)
        self.options_chain = pd.DataFrame()
        self.calls = pd.DataFrame()
        self.puts = pd.DataFrame()
        self.candles = pd.DataFrame()
        self.greeks = Greeks()

        # Formats
        self.date_format = "%Y-%m-%d"
        self.decimal_format = "{:,.2f}"
        self.percent_format = "{:,.0f}%"
        self.percent_format_decimal = "{:,.2f}%"

    """
    ==================================================================================================================================
    Options Chain
    ==================================================================================================================================
    """

    def set_options_chain(self):
        if self.chain_date != "":
            self.options_chain = self.obj.option_chain(self.chain_date)
        else:
            self.options_chain = self.obj.option_chain()
        self.calls = self.options_chain.calls
        self.puts = self.options_chain.puts
        self.calls["option_type"] = "call"
        self.puts["option_type"] = "put"
        self.options_chain = pd.concat([self.calls, self.puts]).reset_index(drop=True)
        self.options_chain = self._apply_options_data(self.options_chain)

    def _apply_options_data(self, option_data: pd.DataFrame):
        candles = self.get_candles()
        option_data["mark"] = (option_data["bid"] + option_data["ask"]) / 2
        option_data["sigma"] = candles["sigma"].iloc[-1]
        option_data["stockPrice"] = candles["Close"].iloc[-1]
        option_data["expirationDate"] = option_data["contractSymbol"].apply(
            self._apply_expiration_date
        )
        option_data["dte"] = option_data["expirationDate"].apply(self._apply_dte)
        option_data["delta"] = option_data.apply(
            lambda row: self.greeks.apply_delta(row), axis=1
        )
        option_data["intrinsic_value"] = option_data.apply(
            lambda row: self._apply_intrinsic_value(row), axis=1
        )
        option_data["extrinsic_value"] = option_data.apply(
            lambda row: self._apply_extrinsic_value(row), axis=1
        )
        option_data["extrinsic_%"] = (
            option_data["extrinsic_value"] / option_data["intrinsic_value"]
        ) * 100
        option_data["extrinsic_%"] = option_data["extrinsic_%"].apply(
            self.decimal_format.format
        )
        option_data["total_value"] = (
            option_data["intrinsic_value"] + option_data["extrinsic_value"]
        )
        option_data["delta"] = option_data["delta"].apply(self.decimal_format.format)
        option_data = option_data.apply(
            lambda row: self.greeks._apply_black_scholes(row), axis=1
        )
        return option_data

    def get_options_chain(self):
        if self.options_chain.empty:
            self.set_options_chain()
        return self.options_chain

    def get_calls(self):
        if self.options_chain.empty:
            self.set_options_chain()
        return self.options_chain.calls

    def get_puts(self):
        if self.options_chain.empty:
            self.set_options_chain()
        return self.options_chain.puts

    def set_candles(self, period: str = "1y"):
        self.candles = yf.download(self.ticker, period=period)
        self.candles.columns = self.candles.columns.droplevel(1)
        prices = self.candles["Close"].to_list()
        log_returns = np.log(np.array(prices[1:]) / np.array(prices[:-1]))
        # Standard deviation of daily log returns
        daily_std = np.std(log_returns)
        # Annualized volatility (sigma)
        sigma = daily_std * np.sqrt(252)
        self.candles["sigma"] = sigma

        # self.candles["log_return"] = np.log(
        #     self.candles["Close"] / self.candles["Close"].shift(1)
        # )
        # daily_vol = self.candles["log_return"].std()
        # annual_vol = daily_vol * np.sqrt(252)
        # print(f"SIGMA: {annual_vol}")
        # self.candles["sigma"] = annual_vol

    def get_candles(self, period: str = "1y") -> pd.DataFrame:
        if self.candles.empty:
            self.set_candles(period)
        return self.candles

    """
    ==================================================================================================================================
    Utilities
    ==================================================================================================================================
    """

    def get_price_to_strike_difference(self, strike_price: float, option_type: str):
        candles = self.get_candles()
        close = candles["Close"].iloc[-1]
        print(f"CLOSE: {close}   STRIKE: {strike_price}")
        if option_type == "call":
            diff = (strike_price - close) / abs(close)
        elif option_type == "put":
            diff = (close - strike_price) / abs(close)
            diff *= -1
        diff *= 100
        return diff

    def find_historical_correlation(self, value: float, window: int, option_type: str):

        df = self.get_candles()
        drop_windows = []
        column = "Close"
        for i in range(len(df) - window + 1):
            start_value = df[column].iloc[i]
            end_value = df[column].iloc[i + window - 1]
            percentage_change = ((end_value - start_value) / start_value) * 100
            if option_type == "put":
                if percentage_change <= -value:
                    drop_windows.append(df.iloc[i : i + window])
                elif percentage_change >= value:
                    drop_windows.append(df.iloc[i : i + window])
        return drop_windows

    def _apply_intrinsic_value(self, row: pd.Series):
        S = row["stockPrice"]
        K = row["strike"]
        option_type = row["option_type"]
        if option_type == "call":
            intrinsic = max(S - K, 0)  # Assing 0 if S - K < 0
        elif option_type == "put":
            intrinsic = max(K - S, 0)
        return intrinsic

    def _apply_extrinsic_value(self, row: pd.Series):
        option_price = row["ask"]
        intrinsic = row["intrinsic_value"]
        extrinsic = option_price - intrinsic
        return extrinsic

    def _apply_expiration_date(self, contract_symbol: str):
        data = self.parse_contract_symbol(contract_symbol, return_tuple=True)
        date = data[1]
        return date

    def _apply_dte(self, date: str):
        current_date = dt.datetime.now()
        date_obj = dt.datetime.strptime(date, self.date_format)
        delta = date_obj - current_date
        return delta.days

    def parse_contract_symbol(self, contract_symbol, return_tuple: bool = False):
        # Regular expression
        pattern = r"(?P<ticker>[A-Z]+)(?P<date>\d{6})(?P<option_type>[CP])(?P<strike_price>\d+)"
        matches = re.match(pattern, contract_symbol)

        if matches:
            ticker = matches.group("ticker")
            date = matches.group("date")
            year = date[:2]
            month = date[2:4]
            day = date[4:]
            date = f"20{year}-{month}-{day}"
            option_type = matches.group("option_type")
            strike_price = float(matches.group("strike_price")) / 1000

            if return_tuple:
                return ticker, date, option_type, strike_price
            else:
                return f"{ticker} | {date} | {option_type} | ${strike_price}"

    """
    ==================================================================================================================================
    Plotting
    ==================================================================================================================================
    """

    def plot_volatility_surface(self):
        pass


class Greeks:
    def __init__(
        self, risk_free_rate: float = 0.0468, auto_risk_free_rate: bool = True
    ) -> None:
        if auto_risk_free_rate:
            self.risk_free_rate = self.get_risk_free_rate()
        else:
            self.risk_free_rate = risk_free_rate

    def get_risk_free_rate(self) -> float:
        ticker = "^TNX"
        data = yf.download(ticker)
        data.columns = data.columns.droplevel(1)
        return data["Close"].iloc[-1] / 100

    def get_delta(self, S, K, T, r, sigma, option_type):
        """
        Calculate the Black-Scholes delta for a call or put option.

        Parameters:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate (annualized)
        sigma (float): Volatility (annualized)
        option_type (str): "call" for call option, "put" for put option

        Returns:
        float: Delta of the option
        """
        # Calculate d1
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            # Calculate delta
            if option_type == "call":
                delta = norm.cdf(d1)  # N(d1) for calls
            elif option_type == "put":
                delta = norm.cdf(d1) - 1  # N(d1) - 1 for puts
            else:
                raise ValueError("Invalid option_type. Use 'call' or 'put'.")
        except ValueError:
            delta = np.nan
        return delta

    def new_delta(self, S, K, T, r, sigma, option_type):
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        if option_type == "call":
            return norm.cdf(d1)  # N(d1)
        elif option_type == "put":
            return norm.cdf(d1) - 1  # N(d1) - 1
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")

    def apply_delta(self, option_data):
        option_type = option_data["option_type"]
        S = option_data["stockPrice"]
        K = option_data["strike"]
        T = option_data["dte"] / 365
        r = self.risk_free_rate
        sigma = option_data["sigma"]

        new_sigma = self.get_implied_sigma(
            S, K, T, r, sigma, q=0, option_type=option_type
        )
        # print(f"S: {S}   K: {K}  T: {T}  R: {r}  SIGMA: {sigma}  NEW: {new_sigma}")
        delta = self.get_delta(S, K, T, r, sigma, option_type)
        return delta

    def get_implied_sigma(self, S, K, T, r, sigma, q, option_type):
        result = minimize(
            self.objective_function,
            sigma,
            args=(S, K, T, r, q, option_type),
            bounds=[(0.01, 3.0)],
        )
        iv = result.x[0]
        return iv

    def objective_function(self, sigma, S, K, T, r, q, option_type: str):
        model_price = self.black_scholes(S, K, T, r, sigma, q, option_type)
        return (model_price - S) ** 2

    def _apply_black_scholes(self, row: pd.Series):
        print(f"ROW: {row}")

        bs = self.black_scholes(
            row["stockPrice"],
            K=row["strike"],
            T=row["dte"] / 365,
            r=0.0465,
            sigma=row["sigma"],
            q=0,
        )

    def black_scholes(self, S, K, T, r, sigma, q, option_type="call"):
        d1 = (np.log(S / K) + (r - q + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type == "call":
            return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type == "put":
            return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(
                -d1
            )
