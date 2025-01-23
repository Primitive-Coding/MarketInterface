import time
import asyncio

# Ticker lists
from LocalStorage.ticker_lists import gmx

from Strategies.pair_trade import PairTrade
from Chart.stock_charts import StockCharts
from Chart.correlation import Correlation

from Chart.stock_charts import StockCharts
from Scrapers.webull import Webull

# Look at this for dex prices: https://coinsbench.com/using-web3-python-to-get-latest-price-of-smart-contract-token-92aafcb2bde7

candle_storage = "./LocalStorage/Candles"


if __name__ == "__main__":
    # s = StockCharts()
    # s.compare_candles(["BTC-USD", "MSTR"], interval="1m", period="max")
    w = Webull()
    w.scrape_gainers(post_market=True)
    # c = Correlation()
    # c.plot_matrix(["AAPL", "MSFT", "RKLB", "BTC-USD", "MSTR"])
    # p = PairTrade("BTC-USD", "MSTR")
    # p.set_data()
    # t1 = ["RKLB", "RDW", "ASTS", "PL", "LUNR"]
    # tickers = ["AAPL", "MSFT", "NVDA", "RKLB"]
    # s.compare_candles(t1)
