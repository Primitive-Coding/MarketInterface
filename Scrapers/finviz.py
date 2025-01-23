import os
import numpy as np
import pandas as pd
from pyfinviz.screener import Screener
from pyfinviz.quote import Quote


income_statement_mapping = {
    "Total Revenue": "Revenue",
    "Cost of Goods Sold Incl. D&A": "COGs",
    "Selling, General and Administrative Excl. Other": "SG&A",
    "Research and Development": "R&D",
    "EPS (Basic, Before Extraordinaries)": "EPS - Basic",
    "EPS (Diluted)": "EPS - Diluted",
    "Price To Earnings Ratio": "P/E",
    "Price To Sales Ratio": "P/S",
}


class Finviz:
    def __init__(
        self, export_path: str = "M:\\Finance\\stocks\\FINVIZ", log_errors: bool = True
    ):
        self.screener = Screener()
        self.log_errors = log_errors
        self.export_dir = export_path

        # Formats
        self.pct_decimal_format = "{:,.2f}%"

    def get_income_statement(self, ticker: str, include_period_length: bool = False):
        """
        Fetch income statement. Will save statements to reduce future queries.

        Parameters
        ----------
        ticker : str
            Ticker of the company to search.
        include_period_length : bool, optional
            Determines if period lenght rows are in dataframe, by default False

        Returns
        -------
        pd.DataFrame
            Dataframe containing information related to the financial statement.
        """
        ticker_dir = f"{self.export_dir}\\{ticker.upper()}"
        os.makedirs(ticker_dir, exist_ok=True)
        path = f"{ticker_dir}\\income_statement.csv"
        try:
            df = pd.read_csv(path)
            df = df.rename(columns={"Unnamed: 0": "index"})
            df.set_index("index", inplace=True)
        except FileNotFoundError:
            df = self.fetch_income_statement(ticker)
            df.to_csv(path)

        if not include_period_length:
            df.drop("Period Length", axis=0, inplace=True)
        df = df.rename(index=income_statement_mapping)
        df.loc["Revenue_Growth"] = self._calc_growth(df.loc["Revenue"].to_list())
        df.loc["Earnings_Growth"] = self._calc_growth(df.loc["Net Income"].to_list())
        return df

    def fetch_income_statement(self, ticker: str):
        """
        Fetch income statement from 'Finviz'.

        Parameters
        ----------
        ticker : str
            Ticker of the company to search.

        Returns
        -------
        pd.DataFrame
            Dataframe containing information related to the financial statement.
        """
        quote = Quote(ticker=ticker.upper())
        # Transpose dataframe. Dates are now columns
        df = quote.income_statement_df.T
        # Set dates as columns
        df.columns = df.iloc[0]
        df = df[1:]
        df = df.iloc[:, ::-1]
        mcap = df.loc["Market Capitalization"].apply(self.str_to_float)
        shares = df.loc["Shares Outstanding"].apply(self.str_to_float)
        df.loc["share_price"] = mcap / shares
        return df

    def get_balance_sheet(self, ticker: str, include_period_length: bool = False):
        """
        Fetch income statement. Will save statements to reduce future queries.

        Parameters
        ----------
        ticker : str
            Ticker of the company to search.
        include_period_length : bool, optional
            Determines if period lenght rows are in dataframe, by default False

        Returns
        -------
        pd.DataFrame
            Dataframe containing information related to the financial statement.
        """
        ticker_dir = f"{self.export_dir}\\{ticker.upper()}"
        os.makedirs(ticker_dir, exist_ok=True)
        path = f"{ticker_dir}\\balance_sheet.csv"
        try:
            df = pd.read_csv(path)
            df = df.rename(columns={"Unnamed: 0": "index"})
            df.set_index("index", inplace=True)
        except FileNotFoundError:
            df = self.fetch_balance_sheet(ticker)
            df.to_csv(path)

        if not include_period_length:
            df.drop("Period Length", axis=0, inplace=True)
        df = df.rename(index=income_statement_mapping)
        return df

    def fetch_balance_sheet(self, ticker: str):
        """
        Fetch balance sheet from 'Finviz'.

        Parameters
        ----------
        ticker : str
            Ticker of the company to search.

        Returns
        -------
        pd.DataFrame
            Dataframe containing information related to the financial statement.
        """
        quote = Quote(ticker=ticker.upper())
        # Transpose dataframe. Dates are now columns
        df = quote.balance_sheet_df.T
        # Set dates as columns
        df.columns = df.iloc[0]
        df = df[1:]
        df = df.iloc[:, ::-1]
        return df

    def get_low_cap_movers(self):
        options = [
            # Screener.AnalystRecomOption.STRONG_BUY_1,
            Screener.MarketCapOption.SMALL_UNDER_USD2BLN,
            Screener.RelativeVolumeOption.OVER_1,
            Screener.CurrentVolumeOption.SHARES_OVER_1M,
        ]
        screener = Screener(
            filter_options=options,
            view_option=Screener.ViewOption.VALUATION,
            pages=[x for x in range(1, 20)],
        )
        df = screener.data_frames
        df = self._convert_frames_many_to_one(df)
        return df

    def _convert_frames_many_to_one(self, data: dict):
        df = pd.DataFrame()
        for k, v in data.items():
            v = self._format_dataframe(v)
            df = pd.concat([df, v], axis=0)

        df.sort_values("Change", ascending=False, inplace=True)
        df.reset_index(inplace=True, drop=True)
        return df

    def _format_dataframe(self, df: pd.DataFrame):
        df = df.set_index("No")
        df["Marketcap_float"] = df["MarketCap"].apply(self._marketcap_to_float)
        df["Change"] = df["Change"].apply(self._format_value)
        df["Volume"] = df["Volume"].apply(self._format_value)
        df["Salespast5Y"] = df["Salespast5Y"].apply(self._format_value)
        df["EPSthisY"] = df["EPSthisY"].apply(self._format_value)
        df["EPSnextY"] = df["EPSnextY"].apply(self._format_value)
        df["EPSpast5Y"] = df["EPSpast5Y"].apply(self._format_value)
        return df

    def _marketcap_to_float(self, mcap):
        label = mcap[-1]
        stripped = float(mcap[:-1])
        if label.upper() == "K":
            val = stripped * 1_000
        elif label.upper() == "M":
            val = stripped * 1_000_000
        elif label.upper() == "B":
            val = stripped * 1_000_000_000
        return val

    def str_to_float(self, value):
        if "," in value:
            value = value.replace(",", "")
        try:
            value = float(value)
        except ValueError:
            value = np.nan
        return value

    def _format_value(self, val, pct_to_dec: bool = False):
        """
        Logic to convert values from a string to a float through various cases.

        Example:
        90% = 90.0 (.90 if 'pct_to_dec' is True)
        1,000,000 -> 1000000.0
        $13.50 -> 13.50

        Parameters
        ----------
        val : str
            Value to convert
        pct_to_dec : bool, optional
            Determines if a percentage value is converted in terms of decimals, by default False

        Returns
        -------
        float
            Input string returned as float.
        """

        try:
            if "%" in val:
                val = val[:-1]
                if pct_to_dec:
                    val = float(val) / 100
                else:
                    val = float(val)
        except Exception as e:
            if self.log_errors:
                print(f"[_format_values (%)]: {e}")
        try:
            if "," in val:
                val = val.replace(",", "")
                val = float(val)
        except Exception as e:
            if self.log_errors:
                print(f"[_format_values (,)]: {e}")
        try:
            if "$" in val:
                val = val[1:]
                val = float(val)
        except Exception as e:
            if self.log_errors:
                print(f"[_format_values ($)]: {e}")
        return val

    def _calc_growth(self, values: list, return_as_percent: bool = True) -> list:
        if type(values) != list:
            values = values.to_list()
        index = 0
        growth = []
        for v in values:
            if index == 0:
                growth.append(np.nan)
            else:
                v2 = values[index - 1]
                v = float(v)
                v2 = float(v2)
                g = (v - v2) / abs(v2)
                if return_as_percent:
                    g *= 100
                    g = self.pct_decimal_format.format(g)
                growth.append(g)
            index += 1
        return growth
