from Screener.top_mover import TopMovers


if __name__ == "__main__":
    tickers = ["AAPL", "MSFT"]

    top = TopMovers()
    top.set_data(tickers, multi_fetch=True, candle_interval="1m")
    data = top.get_data()
    print(f"Data: {data}")
