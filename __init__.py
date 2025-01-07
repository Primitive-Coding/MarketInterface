from Screener.finviz import Finviz
from Crypto.CEX.cex_aggregator import CexAggregator
from Crypto.CEX.cex import CentralizedExchange, free_exchanges


def finviz():
    fin = Finviz()
    df = fin.get_low_cap_movers()
    print(f"DF: {df}")


def CEX():
    agg = CexAggregator(["coinbase", "vertex"])
    # agg.get_last_price("BTC")
    c = agg.aggregate_candles(["BTC", "ETH", "XRP"])
    # print(c)
    # c = CentralizedExchange("coinbase")
    # c.plot("XRP")


if __name__ == "__main__":

    CEX()
