# Compare Similarity

tickers = ["BTC", "ETH", "XRP"]
agg = CexAggregator(["coinbase"])
sim_scores = agg.compare_candles(tickers)

'''
Bitcoin is used for the base comparison (regardless if passed in the 'tickers' list).
Scores will compare coins movement agains Bitcoin.

ticker score
ETH 0.812791
XRP 0.537555

'''
