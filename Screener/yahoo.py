import warnings
import numpy as np
import pandas as pd

# Yahoo python
import yfinance as yf

# Date & Time
import datetime as dt
import pytz

# Sentiment Model

from MachineLearning.NLP.sentiment_analysis import SentimentAnalysis


class YahooAggregator:
    def __init__(self, tickers: str):
        self.tickers = tickers
        self.objs = {t: YahooScreener(t) for t in tickers}

    def get_margins(self, use_ttm: bool = True, use_average: bool = False):
        df = pd.DataFrame()
        for k, v in self.objs.items():
            if use_ttm:
                gross_margin = v.get_gross_margin().iloc[-1] * 100
                op_margin = v.get_operating_margin().iloc[-1] * 100
                net_margin = v.get_net_margin().iloc[-1] * 100
                fcf_margin = v.get_fcf_margin().iloc[-1] * 100
            else:
                gross_margin = v.get_gross_margin().mean() * 100
                op_margin = v.get_operating_margin().mean() * 100
                net_margin = v.get_net_margin().mean() * 100
                fcf_margin = v.get_fcf_margin().mean() * 100
            df.loc[k, "Gross Margin"] = gross_margin
            df.loc[k, "Operating Margin"] = op_margin
            df.loc[k, "Net Margin"] = net_margin
            df.loc[k, "FCF Margin"] = fcf_margin

        df = df.apply(format_percent)
        print(f"DF: {df}")

    def get_growth(self, use_ttm: bool = True, use_average: bool = False):
        df = pd.DataFrame()
        for k, v in self.objs.items():
            rev = v.get_revenue()
            eps = v.get_eps()
            fcf = v.get_fcf()
            rev_growth = (
                v.calc_growth(rev, use_ttm=use_ttm, use_average=use_average) * 100
            )
            eps_growth = (
                v.calc_growth(eps, use_ttm=use_ttm, use_average=use_average) * 100
            )
            fcf_growth = (
                v.calc_growth(fcf, use_ttm=use_ttm, use_average=use_average) * 100
            )
            df.loc[k, "Revenue Growth"] = rev_growth
            df.loc[k, "EPS Growth"] = eps_growth
            df.loc[k, "FCF Growth"] = fcf_growth
        df = df.apply(format_percent)
        return df


class YahooScreener:
    def __init__(self, ticker: str = ""):
        if ticker != "":
            self.ticker = ticker.upper()
            self.obj = yf.Ticker(ticker=self.ticker)
            self.income_statement = self.obj.income_stmt.iloc[
                :, ::-1
            ]  # Reverse columns. Now new dates are on the right.
            self.balance_sheet = self.obj.balance_sheet.iloc[:, ::-1]
            self.cash_flow = self.obj.cash_flow.iloc[:, ::-1]

    """
    ==================================================================================================================================
    Financial Statements
    ==================================================================================================================================
    """
    """
    ==================================================================================================================================
    Income Statement
    ==================================================================================================================================
    """

    def get_revenue(self):
        value = self.income_statement.loc["Total Revenue"]
        return value

    def get_cogs(self):
        value = self.income_statement.loc["Cost Of Revenue"]
        return value

    def get_gross_profit(self):
        value = self.income_statement.loc["Gross Profit"]
        return value

    def get_sga(self):
        value = self.income_statement.loc["Selling General And Administrative"]
        return value

    def get_rnd(self):
        value = self.income_statement.loc["Research And Development"]
        return value

    def get_operating_income(self):
        value = self.income_statement.loc["Operating Income"]
        return value

    def get_net_income(self):
        value = self.income_statement.loc["Net Income"]
        return value

    def get_shares(self, diluted: bool = False):
        if diluted:
            value = self.income_statement.loc["Diluted Average Shares"]
        else:
            value = self.income_statement.loc["Basic Average Shares"]
        return value

    def get_eps(self, diluted: bool = False):
        if diluted:
            value = self.income_statement.loc["Diluted EPS"]
        else:
            value = self.income_statement.loc["Basic EPS"]
        return value

    """
    ==================================================================================================================================
    Balance Sheet 
    ==================================================================================================================================
    """
    """
    ==================================================================================================================================
    Cash Flow
    ==================================================================================================================================
    """

    def get_fcf(self):
        value = self.cash_flow.loc["Free Cash Flow"]
        return value

    """
    ==================================================================================================================================
    Utilities
    ==================================================================================================================================
    """

    def calc_growth(
        self, values: pd.Series, use_ttm: bool = True, use_average: bool = False
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            change = values.pct_change()
        if use_ttm:
            value = change.iloc[-1]
            return value
        if use_average:
            value = change.mean()
            return value

    def _convert_date(self, date, tz: str = "PST"):
        utc_time = dt.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        utc_zone = pytz.utc
        pst_zone = pytz.timezone("US/Pacific")
        # Localize the time to UTC
        utc_time = utc_zone.localize(utc_time)

        # Convert to PST
        pst_time = utc_time.astimezone(pst_zone)
        pst_time = pst_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        return pst_time

    def get_news(self):
        news = self.obj.news
        data = {
            "date": [],
            "id": [],
            "title": [],
            "summary": [],
            "url": [],
            "publisher": [],
        }

        for n in news:
            _id = n["id"]
            content = n["content"]
            title = content["title"]
            summary = content["summary"]
            date = content["pubDate"]
            date = self._convert_date(date)
            url = content["canonicalUrl"]["url"]
            publisher = content["provider"]["displayName"]
            data["date"].append(date)
            data["id"].append(_id)
            data["title"].append(title)
            data["summary"].append(summary)
            data["url"].append(url)
            data["publisher"].append(publisher)
        data = pd.DataFrame(data).set_index("date").iloc[::-1]
        print(f"DATA: {data}")

        return news

    """
    ==================================================================================================================================
    Margins
    ==================================================================================================================================
    """

    def get_gross_margin(self):
        rev = self.get_revenue()
        gp = self.get_gross_profit()
        gross_margin = gp / rev
        return gross_margin

    def get_operating_margin(self):
        rev = self.get_revenue()
        op_inc = self.get_operating_income()
        operating_margin = op_inc / rev
        return operating_margin

    def get_net_margin(self):
        rev = self.get_revenue()
        net_inc = self.get_net_income()
        net_margin = net_inc / rev
        return net_margin

    def get_fcf_margin(self):
        rev = self.get_revenue()
        fcf = self.get_fcf()
        fcf_margin = fcf / rev
        return fcf_margin

    """
    ==================================================================================================================================
    Day Gainers/Losers
    ==================================================================================================================================
    """


"""
==================================================================================================================================
Formatting
==================================================================================================================================
"""


def format_percent(val, decimals: int = 2):
    val_format = f"{{:,.{decimals}f}}%"
    if type(val) == pd.Series:
        tickers = val.index.to_list()
        for t in tickers:
            v = val[t]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", FutureWarning)
                val[t] = val_format.format(v)
        return val
    else:
        val = val_format.format(val)
        return val


if __name__ == "__main__":

    mode = ""

    if mode == "agg":
        tickers = ["NVO", "LLY", "MRNA"]
        ya = YahooAggregator(tickers)
        g = ya.get_growth()
    else:
        ys = YahooScreener("RIVN")
        n = ys.get_news()
        print(f"N: {n}")
