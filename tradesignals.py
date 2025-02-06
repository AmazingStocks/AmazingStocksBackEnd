import yfinance as yf
import pandas as pd
import backtrader as bt
from datetime import datetime, timedelta

# Load tickers from a file
def load_tickers(file_path):
    with open(file_path, "r") as file:
        tickers = [line.strip() for line in file.readlines()]
    return tickers

# Fetch latest stock data from Yahoo Finance
def get_stock_data(ticker, period="6mo", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, multi_level_index=False)
        if not df.empty:
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]  # Ensure required columns
        return df if not df.empty else None
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# Backtrader Strategy for Mean Reversion
class MeanReversionStrategy(bt.Strategy):
    params = (
        ("boll_period", 20),
        ("rsi_period", 14),
        ("rsi_lower", 30),
        ("rsi_upper", 70),
    )
    def __init__(self):
        self.bb = bt.indicators.BollingerBands(period=20)  # Bollinger Bands
        self.rsi = bt.indicators.RSI(period=14)  # RSI Indicator
        self.trade_signals = {}  # Dictionary to track recent buy/sell signals

    def next(self):
        current_date = self.datas[0].datetime.date(0)
        one_week_ago = datetime.now().date() - timedelta(days=7)
        if self.position:
            # Exit conditions: Price returns to the mean (SMA20)
            if self.data.close[0] > self.bb.lines.mid[0]:
                self.close()
                if(one_week_ago <= current_date):
                    print(f"{self.data._name} :- SELL: {self.data.datetime.date(0)} | Price: {self.data.close[0]}")

        else:
            # Buy when price touches lower Bollinger Band & RSI < 30
            if self.data.close[0] <= self.bb.lines.bot[0] and self.rsi[0] < self.params.rsi_lower:
                self.buy()
                if(one_week_ago <= current_date):
                    print(f"{self.data._name} :- BUY: {self.data.datetime.date(0)} | Price: {self.data.close[0]}")

# Run Backtrader Engine
def run_backtest(ticker, df):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MeanReversionStrategy)
    data_feed = bt.feeds.PandasData(dataname=df, name=ticker)
    cerebro.adddata(data_feed)
    cerebro.run()

# Main Function
def main(ticker_file):
    tickers = load_tickers(ticker_file)
    for ticker in tickers:
        df = get_stock_data(ticker)
        if df is not None:
            run_backtest(ticker, df)

# Run the script (Ensure 'tickers.txt' file exists with stock symbols)
if __name__ == "__main__":
    main("tickers.txt")
