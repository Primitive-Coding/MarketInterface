# Yahoo

##### Aggregating Data

tickers = ["NVO", "LLY", "MRNA"]

ya = YahooAggregator(tickers)

ya.get_margins()

    Gross Margin Operating Margin Net Margin FCF Margin

NVO 84.60% 44.16% 36.03% 30.14%
LLY 79.25% 31.61% 15.36% -9.24%
MRNA 30.52% -62.76% -69.80% -56.63%
