import backtrader as bt
import yfinance as yf
import datetime
from yahoo_fin import stock_info as si
import matplotlib
import json


from TradeSignalsAnalyzer import TradeSignalsAnalyzer
from tradingstrategies.MeanReversionStrategy import MeanReversionStrategy
from tradingstrategies.MovingAverageCrossoverStrategy import MovingAverageCrossoverStrategy
matplotlib.use("Agg")  # Use Agg backend for non-GUI environments
import matplotlib.pyplot as plt

def get_all_tickers(segment : str):
    if segment == "nifty50":
        return si.tickers_nifty50()
    elif segment == "niftybank":
        return si.tickers_niftybank()
    elif segment == "nifty100":
        return load_tickers("data/tickers_nifty100.txt")
    elif segment == "nifty500":
        return load_tickers("data/tickers_nifty500.txt")
    
    return si.tickers_nifty50()

# Download Historical Data from Yahoo Finance
def get_data(symbol, period="1y", interval="1d"):
    data = yf.download(symbol, period=period, interval=interval, multi_level_index=False)
    data = data.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    return data

# Custom analyzer to collect trade signals
# Backtest Function modified to return JSON object with trade signals
def backtest(symbol):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MovingAverageCrossoverStrategy, chk_last_weeks=1, symbol=symbol)
    
    # Add custom analyzer
    cerebro.addanalyzer(TradeSignalsAnalyzer, _name="tradesignals")
    
    # Load Data
    df = get_data(symbol)
    data = bt.feeds.PandasData(dataname=df)
    
    # Add data to Cerebro
    cerebro.adddata(data)
    cerebro.broker.set_cash(100000)  # Set initial capital
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)  # Trade with 10% of the available cash per trade

    # Run backtest and get trade signals from the analyzer
    results = cerebro.run()
    signals = results[0].analyzers.tradesignals.get_analysis()
    
    # Optionally, generate plot image (commented out)
    # fig = cerebro.plot()[0][0]
    
    return  signals


def run_backtests(segment : str):
    tickers = get_all_tickers(segment)
    all_signals = {}
    for symbol in tickers:
        try:
            result = backtest(symbol)
            all_signals[symbol] = result
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
    filtered_signals = {symbol: result for symbol, result in all_signals.items() if result and result != []}
    return filtered_signals


# Load tickers from a file
def load_tickers(file_path):
    with open(file_path, "r") as file:
        tickers = [line.strip() for line in file.readlines()]
    return tickers

# Run Backtest for Reliance Industries (NSE)
if __name__ == "__main__":
    tickers = get_all_tickers("nifty100")
    print(tickers)
