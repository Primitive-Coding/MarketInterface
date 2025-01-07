from Screener.finviz import Finviz
from Screener.yahoo import YahooAggregator, YahooScreener
from Crypto.CEX.cex_aggregator import CexAggregator
from Crypto.CEX.cex import CentralizedExchange, free_exchanges


# Ticker lists
from LocalStorage.ticker_lists import gmx


# Look at this for dex prices: https://coinsbench.com/using-web3-python-to-get-latest-price-of-smart-contract-token-92aafcb2bde7


def finviz():
    fin = Finviz()
    df = fin.get_low_cap_movers()
    print(f"DF: {df}")


def CEX():
    tickers = ["BTC", "ETH", "XRP"]
    agg = CexAggregator(["coinbase"])
    sim = agg.compare_candles(gmx)
    print(f"SIM: {sim}")
    # agg.get_last_price("BTC")
    # c = agg.aggregate_candles(gmx, aggregate_columns=True)
    # min_v = agg._find_min_value(c, "spread_200")
    # print(f"C: {min_v}")
    # print(c)
    # c = CentralizedExchange("coinbase")
    # c.plot("XRP")


def YAHOO():
    ys = YahooScreener("RIVN")
    n = ys.get_news()
    print(f"N: {n}")


if __name__ == "__main__":
    YAHOO()
