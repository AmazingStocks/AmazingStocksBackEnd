import backtrader as bt
import yfinance as yf
import datetime
import matplotlib

from tradingstrategies.KNNMovingAverageCrossoverStrategy import KNNMovingAverageCrossoverStrategy
from tradingstrategies.MeanReversionStrategy import MeanReversionStrategy
from tradingstrategies.MovingAverageCrossoverStrategy import MovingAverageCrossoverStrategy
matplotlib.use("Agg")  # Use Agg backend for non-GUI environments
import matplotlib.pyplot as plt

# Download Historical Data from Yahoo Finance
def get_data(symbol, period="2y", interval="1d"):
    data = yf.download(symbol, period=period, interval=interval, multi_level_index=False)
    data = data.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    # data.columns = data.columns.droplevel(0) # Drop the first level (Ticker Names)
    return data

# Backtest Function
def backtest(symbol):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MovingAverageCrossoverStrategy, chk_last_weeks=1, symbol=symbol)

    # Load Data
    df = get_data(symbol)
    data = bt.feeds.PandasData(dataname=df)

    # Add data to Cerebro
    cerebro.adddata(data)
    cerebro.broker.set_cash(100000)  # Set initial capital
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  # Number of shares per trade

    cerebro.run()

    # Save the plot as an image file instead of displaying it
    fig = cerebro.plot()[0][0]
    fig.savefig(f"backtest_images/backtest_plot_{symbol}.png")  # Save as PNG file

def main(filepath):
    tickers = load_tickers(filepath)
    for symbol in tickers:
        backtest(symbol)
    
    
    
# Load tickers from a file
def load_tickers(file_path):
    with open(file_path, "r") as file:
        tickers = [line.strip() for line in file.readlines()]
    return tickers

# Run Backtest for Reliance Industries (NSE)
if __name__ == "__main__":
    main("tickers.txt")
