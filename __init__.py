import time
import asyncio

from Screener.finviz import Finviz
from Screener.yahoo import YahooAggregator, YahooScreener
from Crypto.CEX.cex_aggregator import CexAggregator
from Crypto.CEX.cex import CentralizedExchange, free_exchanges
from Options.options import Options

from Crypto.Leverage.leverage_scanner import LeverageScanner
from MachineLearning.NN.trailing_candles import Dataset, prepare_data

# Ticker lists
from LocalStorage.ticker_lists import gmx


# Look at this for dex prices: https://coinsbench.com/using-web3-python-to-get-latest-price-of-smart-contract-token-92aafcb2bde7

candle_storage = "./LocalStorage/Candles"


def finviz():
    fin = Finviz()
    df = fin.get_low_cap_movers()
    print(f"DF: {df}")


def CEX():
    tickers = ["BTC", "ETH", "XRP"]
    c = CentralizedExchange("coinbase")
    data = {}
    for t in tickers:
        i = c.fetch_candles(t)
        i.to_csv(f"{candle_storage}/{t}_n.csv")
    return data


async def CEX_A():
    c = CentralizedExchange("coinbase")
    tickers = ["BTC", "ETH", "XRP"]
    ticker_data = await c.async_fetch_multiple_candles(tickers)
    print(f"TICKER: {ticker_data}")
    data = {}
    for symbol, candle in zip(tickers, ticker_data):
        data[symbol] = await candle
        await candle.to_csv(f"{candle_storage}/{symbol}_a.csv")
    return data


def YAHOO():
    ys = YahooScreener("RIVN")
    n = ys.get_news()
    print(f"N: {n}")


def OPTIONS():
    op = Options("RIVN")
    c = op.get_options_chain()


def ML():
    prepare_data()


if __name__ == "__main__":
    # lev = LeverageScanner("coinbase")
    # lev.set_ticker_data(["BTC", "ETH", "XRP"])
    # lev.plot()
    # start = time.time()
    # asyncio.run(CEX_A())
    # end = time.time()
    # elapse = end - start
    # print(f"ELAPSE: {elapse}")
    ML()
