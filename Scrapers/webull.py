import time

# Data
import numpy as np
import pandas as pd


from Scrapers.scraper import Scraper


class Webull(Scraper):
    def __init__(self) -> None:
        self.urls = {
            "gainers": "https://www.webull.com/quote/us/gainers",
            "losers": "https://www.webull.com/quote/us/dropers",
        }
        super().__init__()

    def scrape_gainers(self, pre_market: bool = False, post_market: bool = False):
        url = self.urls["gainers"]
        if pre_market:
            url += "/pre"
        elif post_market:
            url += "/after"
        else:
            url += "/1d"
        table = self._scrape_table(url)
        return table

    def scrape_losers(self, pre_market: bool = False, post_market: bool = False):
        url = self.urls["losers"]
        if pre_market:
            url += "/pre"
        elif post_market:
            url += "/after"
        else:
            url += "/1d"
        table = self._scrape_table(url)
        return table

    def _scrape_table(
        self, url: str, table_label: str = "table-body", num_cols: int = 10
    ) -> pd.DataFrame:
        if self.browser == None:
            self.create_browser(url)
        data = self.read_data_by_classname(table_label, wait=True)
        # Split data
        data = data.split("\n")
        index = 0
        num_cols = 10
        tracking_index = 0
        table_data = {
            "ticker": [],
            "name": [],
            "price": [],
            "change": [],
            "pe": [],
            "marketcap": [],
        }
        magnitudes = ["M", "B"]
        while True:
            section = data[index : index + (num_cols + 1)]
            try:
                mcap = section[-1]
            except IndexError:
                break
            mag_found = False
            for m in magnitudes:
                if m in mcap:
                    mag_found = True

            if not mag_found:
                section = data[index : index + (num_cols + 2)]
                ticker = section[3]
                name = section[2]
                price = section[5]
                change = section[4]
                index += 1
            else:
                ticker = section[2]
                name = section[1]
                price = section[4]
                change = section[3]
            pe = section[-2]
            mcap = section[-1]
            if section == [] or len(section) < (num_cols + 1):
                print(f"BREAK TRIGGERED")
                break
            table_data["ticker"].append(ticker)
            table_data["name"].append(name)
            table_data["price"].append(price)
            table_data["change"].append(change)
            table_data["pe"].append(pe)
            table_data["marketcap"].append(mcap)
            index = index + (num_cols + 1)
            tracking_index += 1
        df = pd.DataFrame(table_data).set_index("ticker")
        df["marketcap"] = df["marketcap"].apply(self._format_str_to_float)
        return df

    def _format_str_to_float(self, value: str):
        print(f"Value: {value}")
        if value == "--" or value == "-":
            return np.nan
        else:
            label = value[-1]
            value = float(value[:-1])

            if label == "M":
                value *= 1_000_000
            elif label == "B":
                value *= 1_000_000_000

            return value
