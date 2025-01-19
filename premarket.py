from Screener.top_mover import TopMovers
from Scrapers.yahoo import YahooScraper

if __name__ == "__main__":
    tickers = ["AAPL", "MSFT"]

    top = TopMovers()
    tickers_losers = top.yahoo.get_day_losers()
    tickers_gainers = top.yahoo.get_day_gainers()
    print(f"Ticker: {tickers_gainers}")
    top.set_metrics(tickers, show_percent_values=False)
    print(top.get_metrics())
    # top.set_data(tickers, multi_fetch=True, candle_interval="1m")
    # data = top.get_data()
    # print(f"Data: {data}")
