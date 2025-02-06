import yfinance as yf
import pandas as pd
import numpy as np
import backtrader as bt
from datetime import datetime, timedelta

# List of tickers (Basket of Stocks)
tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS"]

# Fetch Historical Data
def fetch_data(tickers, start="2020-01-01", end="2025-01-01"):
    data_dict = {}
    for ticker in tickers:
        df = yf.download(ticker, start=start, end=end, multi_level_index=False)
        if not df.empty:
            df['Ticker'] = ticker  # Add Ticker Column
            data_dict[ticker] = df
    return data_dict

# Mean Reversion Strategy
class MeanReversionStrategy(bt.Strategy):
    params = (
        ('bollinger_period', 20),
        ('rsi_period', 14),
        ('rsi_lower', 30),
        ('rsi_upper', 70),
    )

    def __init__(self):
        self.bb = bt.indicators.BollingerBands(period=self.params.bollinger_period)
        self.rsi = bt.indicators.RSI(period=self.params.rsi_period)

    def next(self):
        if not self.position:
            if self.data.close[0] <= self.bb.lines.bot[0] and self.rsi[0] < self.params.rsi_lower:
                self.buy()
                print(f"BUY: {self.data._name} at {self.data.close[0]} on {self.datas[0].datetime.date(0)}")
        else:
            if self.data.close[0] >= self.bb.lines.top[0] and self.rsi[0] > self.params.rsi_upper:
                self.sell()
                print(f"SELL: {self.data._name} at {self.data.close[0]} on {self.datas[0].datetime.date(0)}")

# Run Backtest
def run_backtest(tickers):
    # Fetch and preprocess data
    data_dict = fetch_data(tickers)
    
    # Initialize Backtrader
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MeanReversionStrategy)

    # Add multiple tickers to Backtrader
    for ticker, df in data_dict.items():
        data_feed = bt.feeds.PandasData(dataname=df, name=ticker)
        cerebro.adddata(data_feed)

    # Set initial cash
    cerebro.broker.set_cash(100000)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% brokerage

    # Run backtest
    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")

# Execute the Backtest
if __name__ == "__main__":
    run_backtest(tickers)
