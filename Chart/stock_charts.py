import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt


class StockCharts:
    def __init__(self) -> None:
        pass

    def compare_candles(self, tickers: list, interval: str = "1d", period: str = "1y"):
        candles = yf.download(tickers, interval=interval, period=period)["Close"]
        data = pd.DataFrame()
        for t in tickers:
            values = candles[t]
            anchor_value = values.iloc[0]
            change = ((values - anchor_value) / anchor_value) * 100
            data[t] = change
        self.plot_dataframe(
            data, "Candle Comparison", "Dates", "% Change", "Stock Candles", "line"
        )

    def compare_growth(
        self, tickers: list, revenue: bool = True, earnings: bool = True
    ):
        data = {"Ticker": tickers, "MCAP": []}
        for t in tickers:
            obj = yf.Ticker(t)
            info = obj.info
            mcap = info["marketCap"]
            try:
                r_growth = info["revenueGrowth"] * 100
            except KeyError:
                r_growth = np.nan
            try:
                e_growth = info["earningsGrowth"] * 100
            except KeyError:
                e_growth = np.nan
            if revenue:
                try:
                    data["Revenue"].append(r_growth)
                except KeyError:
                    data["Revenue"] = [r_growth]
            if earnings:
                try:
                    data["Earnings"].append(e_growth)
                except KeyError:
                    data["Earnings"] = [e_growth]
            data["MCAP"].append(mcap)

        df = pd.DataFrame(data).set_index("Ticker")
        df.sort_values("MCAP", axis=0, inplace=True, ascending=False)
        df.drop("MCAP", axis=1, inplace=True)
        self.plot_dataframe(
            df,
            "Growth Comparison",
            "Ticker",
            "Growth",
            "Growth Types",
        )

    def compare_ratios(
        self,
        tickers: list,
        ps: bool = True,
        pe: bool = True,
        forward_pe: bool = False,
        peg: bool = False,
        pb: bool = True,
        pfcf: bool = True,
    ):
        """
        Compare financial ratios amongst companies.

        Parameters
        ----------
        tickers : list
            Tickers of companies to compare ratios with.
        ps : bool, optional
            Price-to-Sales Ratio (TTM), by default True
        pe : bool, optional
            Price-to-Earnings Ratio, by default True
        forward_pe : bool, optional
            Forward Price-to-Earnings Ratio, by default False
        peg : bool, optional
            Price-to-Earnings-Growth, by default False
        pb : bool, optional
            Price-to-Book, by default True
        pfcf : bool, optional
            Price-to-Free-Cash-Flow, by default True
        """
        data = {
            "Ticker": tickers,
            "MCAP": [],
        }
        for t in tickers:
            obj = yf.Ticker(t)
            info = obj.info
            mcap = info["marketCap"]
            if ps:
                ps_val = info["priceToSalesTrailing12Months"]
                try:
                    data["P/S"].append(ps_val)
                except KeyError:
                    data["P/S"] = [ps_val]
            if pe:
                try:
                    pe_val = info["trailingPE"]
                except KeyError:
                    pe_val = np.nan
                try:
                    data["P/E"].append(pe_val)
                except KeyError:
                    data["P/E"] = [pe_val]

            if forward_pe:
                try:
                    fpe = info["forwardPE"]
                except KeyError:
                    fpe = np.nan
                try:
                    data["Forward P/E"].append(fpe)
                except KeyError:
                    data["Forward P/E"] = [fpe]
            if peg:
                peg_val = info["trailingPegRatio"]
                try:
                    data["PEG"].append(peg_val)
                except KeyError:
                    data["PEG"] = [peg_val]
            if pb:
                try:
                    pb_val = info["priceToBook"]
                except KeyError:
                    pb_val = np.nan
                try:
                    data["P/B"].append(pb_val)
                except KeyError:
                    data["P/B"] = [pb_val]
            if pfcf:
                pfcf_val = mcap / info["freeCashflow"]
                try:
                    data["P/FCF"].append(pfcf_val)
                except KeyError:
                    data["P/FCF"] = [pfcf_val]
            data["MCAP"].append(mcap)

        df = pd.DataFrame(data).set_index("Ticker")
        df.sort_values("MCAP", axis=0, inplace=True, ascending=False)
        df.drop("MCAP", axis=1, inplace=True)
        self.plot_dataframe(
            df,
            "Comparison of Financial Ratios",
            "Ticker",
            "Ratio",
            "Ratio Types",
        )

    def compare_margins(self, tickers: list):
        data = {
            "Ticker": tickers,
            "Gross Margin": [],
            "Operating Margin": [],
            "Net Margin": [],
            "MCAP": [],
        }
        for t in tickers:
            obj = yf.Ticker(t)
            info = obj.info
            mcap = info["marketCap"]
            gross = info["grossMargins"] * 100
            operating = info["operatingMargins"] * 100
            net = info["profitMargins"] * 100
            data["Gross Margin"].append(gross)
            data["Operating Margin"].append(operating)
            data["Net Margin"].append(net)
            data["MCAP"].append(mcap)
        # Create a DataFrame for better handling
        df = pd.DataFrame(data).set_index("Ticker")
        df.sort_values("MCAP", axis=0, inplace=True, ascending=False)
        df.drop("MCAP", axis=1, inplace=True)
        self.plot_dataframe(
            df,
            "Comparison of Gross and Operating Margins",
            "Ticker",
            "Margin",
            "Margin Types",
        )
        # Set the index to Ticker for easier plotting

    def plot_dividends(self, ticker: str, freq: int = 4):
        candles = yf.download(ticker.upper(), multi_level_index=False)
        ticker = yf.Ticker(ticker.upper())
        dividends = ticker.history(period="max")["Dividends"]
        dividends = dividends[dividends > 0]
        df = dividends.to_frame()
        for i, row in dividends.items():
            formatted_date = pd.to_datetime(i).strftime("%Y-%m-%d")
            try:
                stock_price = candles.loc[formatted_date, "Close"]
                value = (row / stock_price) * 100
                annual_yield = value * freq
            except KeyError:
                value = np.nan
                annual_yield = np.nan
            df.loc[i, "Yield"] = value
            df.loc[i, "Annual_Yield"] = annual_yield

        # --- Plotting ---
        # Values used for x axis.
        x = df.index
        y1 = df["Dividends"]  # First line (Yield)
        y2 = df["Yield"]  # Second line (Close price)

        plt.figure(figsize=(10, 5))
        plt.plot(x, y1, label="Value($)", color="blue")  # First line
        plt.plot(x, y2, label="Yield(%)", color="red", linestyle="--")  # Second line
        plt.title(f"Dividend Value and Yield for {ticker}")
        plt.xlabel("Date")
        plt.ylabel("Value")
        plt.legend()
        plt.grid()
        plt.show()

    def compare_financial_health(
        self,
        tickers: list,
        roa: bool = True,
        roe: bool = True,
        current_ratio: bool = True,
    ):
        data = {"Ticker": tickers, "MCAP": []}
        for t in tickers:
            obj = yf.Ticker(t)
            info = obj.info
            mcap = info["marketCap"]

            if roa:
                try:
                    roa_val = info["returnOnAssets"]
                except KeyError:
                    roa_val = np.nan
                try:
                    data["ROA"].append(roa_val)
                except KeyError:
                    data["ROA"] = [roa_val]
            if roe:
                try:
                    roe_val = info["returnOnEquity"]
                except KeyError:
                    roe_val = np.nan
                try:
                    data["ROE"].append(roe_val)
                except KeyError:
                    data["ROE"] = [roe_val]
            if current_ratio:
                try:
                    c_val = info["currentRatio"]
                except KeyError:
                    c_val = np.nan
                try:
                    data["Current Ratio"].append(c_val)
                except KeyError:
                    data["Current Ratio"] = [c_val]
            data["MCAP"].append(mcap)
        df = pd.DataFrame(data).set_index("Ticker")
        df.sort_values("MCAP", axis=0, inplace=True, ascending=False)
        df.drop("MCAP", axis=1, inplace=True)
        self.plot_dataframe(
            df,
            "Financial Health Comparison",
            "Ticker",
            "Value",
            "Health Metrics",
        )

    def plot_dataframe(
        self,
        df: pd.DataFrame,
        title: str,
        xlabel: str,
        ylabel: str,
        legend_title: str,
        kind: str = "bar",
        include_grid: bool = True,
        grid_axis: str = "y",
        rotation: int = 0,
        figsize: tuple = (10, 5),
    ):
        # Plotting
        df.plot(kind=kind, figsize=figsize)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation=rotation)  # Rotate x labels for better readability
        plt.legend(title=legend_title)
        if include_grid:
            plt.grid(axis=grid_axis)
        plt.show()
