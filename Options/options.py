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
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker.upper()
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
        self.options_chain = self.obj.option_chain()
        self.calls = self._apply_options_data(self.options_chain.calls, "call")
        self.puts = self._apply_options_data(self.options_chain.puts, "put")

        print(f"CALLS: {self.calls}")

    def _apply_options_data(self, option_data: pd.DataFrame, option_type: str):
        candles = self.get_candles()
        option_data["sigma"] = candles["sigma"].iloc[-1]
        option_data["stockPrice"] = candles["Close"].iloc[-1]
        option_data["expirationDate"] = option_data["contractSymbol"].apply(
            self._apply_expiration_date
        )
        option_data["dte"] = option_data["expirationDate"].apply(self._apply_dte)
        option_data["delta"] = option_data.apply(
            lambda row: self.greeks.apply_delta(row, option_type), axis=1
        )
        option_data["delta"] = option_data["delta"].apply(self.decimal_format.format)
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

    def _apply_expiration_date(self, contract_symbol: str):
        data = self.parse_contract_symbol(contract_symbol)
        date = data[1]
        return date

    def _apply_dte(self, date: str):
        current_date = dt.datetime.now()
        date_obj = dt.datetime.strptime(date, self.date_format)

        delta = date_obj - current_date
        return delta.days

    def parse_contract_symbol(self, contract_symbol):
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

            return ticker, date, option_type, strike_price


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
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        # Calculate delta
        if option_type == "call":
            delta = norm.cdf(d1)  # N(d1) for calls
        elif option_type == "put":
            delta = norm.cdf(d1) - 1  # N(d1) - 1 for puts
        else:
            raise ValueError("Invalid option_type. Use 'call' or 'put'.")
        return delta

    def apply_delta(self, option_data, option_type: str):
        S = option_data["stockPrice"]
        K = option_data["strike"]
        T = option_data["dte"] / 365
        r = self.risk_free_rate
        sigma = option_data["sigma"]

        new_sigma = self.get_implied_sigma(
            S, K, T, r, sigma, q=0, option_type=option_type
        )
        print(f"S: {S}   K: {K}  T: {T}  R: {r}  SIGMA: {sigma}  NEW: {new_sigma}")
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

    def black_scholes(self, S, K, T, r, sigma, q, option_type="call"):
        d1 = (np.log(S / K) + (r - q + (sigma**2) / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type == "call":
            return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type == "put":
            return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(
                -d1
            )
