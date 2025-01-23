# Data
import re
import numpy as np
import pandas as pd
from scipy.stats import norm

# Stock
import yfinance as yf


class OptionScalping:
    def __init__(self) -> None:
        self.option_chain = pd.DataFrame()
        self.calls = pd.DataFrame()
        self.puts = pd.DataFrame()
        self.candles = pd.DataFrame()
        self.stock_price = None
        self.risk_free_rate = None

    # ---------- Options Chain ---------- #
    def set_chain(self, ticker: str, expiration_date: str = ""):
        stock = yf.Ticker(ticker.upper())
        if expiration_date == "":
            self.option_chain = stock.option_chain()
        else:
            self.option_chain = stock.option_chain(expiration_date)

    # ---------- Candles ---------- #
    def set_candles(self, ticker: str):
        self.candles = yf.download(ticker, multi_level_index=False)

    def get_candles(self, ticker: str):
        if self.candles.empty:
            self.set_candles(ticker)
        return self.candles

    # ---------- Stock Price ---------- #
    def set_stock_price(self, ticker: str):
        candles = self.get_candles(ticker)
        self.stock_price = candles["Close"].iloc[-1]

    def get_stock_price(self, ticker: str):
        if self.stock_price == None:
            self.set_stock_price(ticker)
        return self.stock_price

    # ---------- Risk Free Rate ---------- #
    def set_risk_free_rate(self, ticker: str = "^TNX"):
        self.risk_free_rate = yf.download(ticker, multi_level_index=False)
        self.risk_free_rate = self.risk_free_rate["Close"].iloc[-1]

    def get_risk_free_rate(self, ticker: str = "^TNX"):
        if self.risk_free_rate == None:
            self.set_risk_free_rate(ticker)
        return self.risk_free_rate

    # ---------- Calls ---------- #
    def set_calls(self, ticker: str, expiration_date: str = "") -> pd.DataFrame:
        if self.option_chain.empty:
            self.set_chain(ticker, expiration_date)
        self.calls = self.option_chain.calls

    def get_calls(self, ticker: str, expiration_date: str = "") -> pd.DataFrame:
        if self.calls.empty:
            self.set_calls(ticker, expiration_date)
        stock_price = self.get_stock_price(ticker)
        risk_free_rate = self.get_risk_free_rate()
        self.calls["delta"] = self.calls.apply(
            lambda row: self.calculate_row_delta(row, stock_price, risk_free_rate),
            axis=1,
        )
        return self.calls

    # ---------- Puts ---------- #
    def set_puts(self, ticker: str, expiration_date: str = ""):
        if self.option_chain.empty:
            self.set_chain(ticker, expiration_date)
        self.puts = self.option_chain.puts

    def get_puts(self, ticker: str, expiration_date: str = ""):
        if self.puts.empty:
            self.set_puts(ticker, expiration_date)
        stock_price = self.get_stock_price(ticker)
        risk_free_rate = self.get_risk_free_rate()
        self.puts["delta"] = self.puts.apply(
            lambda row: self.calculate_row_delta(row, stock_price, risk_free_rate),
            axis=1,
        )
        return self.puts

    # ---------- Delta ---------- #
    def calculate_row_delta(self, row, S, r):
        return self.calculate_delta(
            S=S,
            K=row["strike"],
            T=row["timeToExpiration"],
            r=r,
            sigma=row["impliedVolatility"],
            option_type="call" if "C" in row["contractSymbol"] else "put",
        )

    def calculate_delta(self, S, K, T, r, sigma, option_type="call"):
        """
        Calculate Delta using the Black-Scholes formula.

        Parameters:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate
        sigma (float): Implied volatility (as a decimal, e.g., 0.25 for 25%)
        option_type (str): 'call' or 'put'

        Returns:
        float: Delta value
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        if option_type == "call":
            return norm.cdf(d1)  # Call Delta
        elif option_type == "put":
            return norm.cdf(d1) - 1  # Put Delta
        else:
            raise ValueError("Invalid option_type. Use 'call' or 'put'.")

    # ---------- Expiration Dates ---------- #
    # NOTE: OPEN CHATGPT
