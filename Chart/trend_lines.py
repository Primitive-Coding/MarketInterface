import requests
import pandas as pd
from bs4 import BeautifulSoup
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress


def get_finviz_data(ticker):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to load page: {url}")
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="snapshot-table2")
    if not table:
        raise Exception("Unable to find data table on the page")
    data = {}
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        for i in range(0, len(cols), 2):
            key = cols[i].text.strip()
            value = cols[i + 1].text.strip().replace("%", "")
            data[key] = value
    return data


def get_yfinance_data(ticker):
    stock = yf.Ticker(ticker)
    months = input(
        "Enter period ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'ytd', 'max']: "
    ).upper()
    try:
        hist = stock.history(period=months)  # Fetch data
    except Exception as e:
        print(f"Error: {e}")
    return stock, hist


def calculate_sharpe_ratio(hist):
    returns = hist["Close"].pct_change()
    avg_return = np.mean(returns)
    std_dev = np.std(returns)
    if std_dev == 0:
        return "N/A"
    sharpe_ratio = avg_return / std_dev * np.sqrt(252)  # Annualized Sharpe Ratio
    return round(sharpe_ratio, 2)


def calculate_support_resistance(hist):
    close_prices = hist["Close"]
    levels = {
        "Support Level 1": np.percentile(close_prices, 20),
        "Resistance Level 1": np.percentile(close_prices, 80),
        "Support Level 2": np.percentile(close_prices, 10),
        "Resistance Level 2": np.percentile(close_prices, 90),
        "Support Level 3": np.percentile(close_prices, 5),
        "Resistance Level 3": np.percentile(close_prices, 95),
    }
    return {key: round(value, 2) for key, value in levels.items()}


def calculate_short_volume_ratio(current_short_volume, short_volume_sma):
    try:
        current_short_volume = float(current_short_volume.replace(",", ""))
        short_volume_sma = float(short_volume_sma.replace(",", ""))
        if short_volume_sma <= 0:
            return "N/A"
        return round(current_short_volume / short_volume_sma, 2)
    except (ValueError, TypeError):
        return "N/A"


def find_swing_points(data, window=5):
    """
    Identify swing highs and lows in price data.
    """
    swing_highs = []
    swing_lows = []
    for i in range(window, len(data) - window):
        high_window = data[i - window : i + window + 1]
        low_window = data[i - window : i + window + 1]
        if data[i] == max(high_window):
            swing_highs.append((i, data[i]))
        if data[i] == min(low_window):
            swing_lows.append((i, data[i]))
    return swing_highs, swing_lows


def plot_stock_data_with_trendlines_and_support(hist, support_resistance):
    plt.figure(figsize=(12, 6))
    plt.style.use("dark_background")  # Use dark background for the plot

    close_prices = hist["Close"].values
    dates = hist.index

    # Plot original support and resistance levels
    for level, price in support_resistance.items():
        color = "lime" if "Support" in level else "red"
        plt.axhline(
            y=price,
            linestyle="--",
            label=f"{level}: {price:.2f}",
            color=color,
            linewidth=1.5,
        )

    # Find swing points
    swing_highs, swing_lows = find_swing_points(close_prices)

    # Plot price data
    plt.plot(dates, close_prices, label="Close Price", color="cyan", linewidth=2)

    # Draw trend lines by connecting swing points
    if len(swing_highs) > 1:
        swing_high_indices = [x[0] for x in swing_highs]
        swing_high_prices = [x[1] for x in swing_highs]
        plt.plot(
            dates[swing_high_indices],
            swing_high_prices,
            color="magenta",
            linestyle="--",
            label="Resistance Line",
        )
    if len(swing_lows) > 1:
        swing_low_indices = [x[0] for x in swing_lows]
        swing_low_prices = [x[1] for x in swing_lows]
        plt.plot(
            dates[swing_low_indices],
            swing_low_prices,
            color="yellow",
            linestyle="--",
            label="Support Line",
        )

    # Customize the plot
    plt.title("Stock Price with Trend Lines", color="white", fontsize=16)
    plt.xlabel("Date", color="white", fontsize=14)
    plt.ylabel("Price", color="white", fontsize=14)
    plt.tick_params(
        axis="x", colors="white", labelsize=12
    )  # Set x-axis tick color and size
    plt.tick_params(
        axis="y", colors="white", labelsize=12
    )  # Set y-axis tick color and size
    plt.legend(facecolor="black", edgecolor="white", fontsize=10)
    plt.grid(color="gray", linestyle="--", linewidth=0.5)
    plt.show()


def analyze_stock(ticker):
    # Fetch data
    finviz_data = get_finviz_data(ticker)
    stock, hist = get_yfinance_data(ticker)
    sharpe_ratio = calculate_sharpe_ratio(hist)
    support_resistance = calculate_support_resistance(hist)

    # Extract Volume, Last Price, and Shares Outstanding
    volume = finviz_data.get("Volume", "N/A")
    shares_outstanding = finviz_data.get("Shs Outstand", "N/A")

    # WIP - Obtaining short data
    current_short_volume = finviz_data.get(
        "Short Float", "N/A"
    )  # Replace with actual short volume data source
    short_volume_sma = (
        "5000000"  # Placeholder: Replace with actual SMA data for short volume
    )

    # Calculate Short Volume to SMA ratio
    short_volume_to_sma = calculate_short_volume_ratio(
        current_short_volume, short_volume_sma
    )

    # Filtered Metrics
    filtered_data = {
        "Ticker": ticker,
        "Last Price": finviz_data.get("Price", "N/A"),
        "Day Change": finviz_data.get("Change", "N/A"),
        "P/E": finviz_data.get("P/E", "N/A"),
        "52-week High (%)": finviz_data.get("52W High", "N/A"),
        "52-week Low (%)": finviz_data.get("52W Low", "N/A"),
        "52-week Range": finviz_data.get("52W Range", "N/A"),
        "RSI": finviz_data.get("RSI (14)", "N/A"),
        "SMA20": finviz_data.get("SMA20", "N/A"),
        "SMA50": finviz_data.get("SMA50", "N/A"),
        "SMA200": finviz_data.get("SMA200", "N/A"),
        "Volatility": finviz_data.get("Volatility", "N/A"),
        "ATR (14)": finviz_data.get("ATR (14)", "N/A"),
        "Earnings": finviz_data.get("Earnings", "N/A"),
        "Market Cap": finviz_data.get("Market Cap", "N/A"),
        "Option/Short": finviz_data.get("Option/Short", "N/A"),
        "Daily Volume": finviz_data.get("Volume", "N/A"),
        "Shares Outstanding": shares_outstanding,
        "Short Volume to SMA": short_volume_to_sma,
        **support_resistance,
    }

    # Additional Analysis
    additional_analysis = {
        "News Sentiment": "Positive",  # Work in progress
        "Social Sentiment": "Neutral",  # Work in progress
        "Sharpe Ratio": sharpe_ratio,
        "Trend": (
            "Bullish (RSI > 70)"
            if float(finviz_data.get("RSI (14)", 50)) > 70
            else "Neutral (RSI <= 70)"
        ),
    }

    # Display Summary
    print("\nClassification Summary:")
    print(
        "RSI: Indicates overbought (>70), oversold (<30), or neutral (30-70) conditions."
    )
    print("Volatility: Measures price variability; higher values suggest greater risk.")
    print("ATR: Average True Range measures price movement; no strict thresholds.")
    print(
        "Short Volume to SMA: A ratio >1 suggests higher shorting activity relative to moving average."
    )

    print("\nMetric               Value")
    for key, value in filtered_data.items():
        print(f"{key:20} {value}")

    print("\n--- Additional Analysis ---")
    print("News Sentiment: Indicates the sentiment from recent headlines.")
    print(f"  Value: {additional_analysis['News Sentiment']}")
    print("Social Sentiment: Refers to mentions and sentiment on social media.")
    print(f"  Value: {additional_analysis['Social Sentiment']}")
    print("Sharpe Ratio: A measure of risk-adjusted return (higher is better).")
    print(f"  Value: {additional_analysis['Sharpe Ratio']}")
    print("Trend: Indicates the stock's current trend based on RSI.")
    print(f"  Value: {additional_analysis['Trend']}")

    # Show Chart
    plot_stock_data_with_trendlines_and_support(hist, support_resistance)


# Prompt user
ticker = input("Enter the stock ticker symbol: ").upper()
try:
    analyze_stock(ticker)
except Exception as e:
    print(f"Error: {e}")
