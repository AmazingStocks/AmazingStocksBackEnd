import backtrader as bt
import yfinance as yf
import datetime
from yahoo_fin import stock_info as si
import matplotlib
import threading
import json
import uuid

from firestore_util import create_document, update_document, get_collection, get_document, delete_document


from TradeSignalsAnalyzer import TradeSignalsAnalyzer
from tradingstrategies.MeanReversionStrategy import MeanReversionStrategy
from tradingstrategies.MovingAverageCrossoverStrategy import MovingAverageCrossoverStrategy
matplotlib.use("Agg")  # Use Agg backend for non-GUI environments
import matplotlib.pyplot as plt

def get_all_tickers(segment_or_symbol : str):
    
    if segment_or_symbol == "nifty50":
        return si.tickers_nifty50()
    elif segment_or_symbol == "niftybank":
        return si.tickers_niftybank()
    elif segment_or_symbol == "nifty100":
        return load_tickers("data/tickers_nifty100.txt")
    elif segment_or_symbol == "nifty500":
        return load_tickers("data/tickers_nifty500.txt")
    
    return si.tickers_nifty50()

def get_data_multiple_symbols(symbols, period="1y", interval="1d"):
    data = None
    try:
        data = yf.download(symbols,group_by='ticker', period=period, interval=interval, multi_level_index=False, progress=False)
    except Exception as e:
        print(f"Error downloading data  {e}")
    return data

def extract_single_ticker_data(symbol, data):   
    if symbol in data:
        df = data[symbol].copy()
        df = df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        })
        return df
    else:
        print(f"No data found for {symbol}")
        return None
    
    

# Download Historical Data from Yahoo Finance
def get_data(symbol, period="1y", interval="1d"):
    data = yf.download(symbol, period=period, interval=interval, multi_level_index=False,progress=False)
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
def backtest(symbol, data, single=False, chk_last_weeks=1):
    """
    Backtest function to run the Moving Average Crossover strategy.
    """     
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MovingAverageCrossoverStrategy, chk_last_weeks=chk_last_weeks, symbol=symbol)
    
    # Add custom analyzer
    cerebro.addanalyzer(TradeSignalsAnalyzer, _name="tradesignals")
    
    # Load Data
    if single:
        df = data.copy()
    else:
        df = extract_single_ticker_data(symbol, data)
    if df is None:
        print(f"No data found for {symbol}")
        raise ValueError(f"No data found for {symbol}")
    
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


def async_backtest(segment: str, process_id, single: bool = False):
    """
    Asynchronous backtest function to run in a separate thread.
    """
    if single:
        data = get_data(segment)
        tickers = [segment]
    else:
        tickers = get_all_tickers(segment)
        data = get_data_multiple_symbols(tickers)
    try:
        all_signals = {}
        for symbol in tickers:
            try:
                result = backtest(symbol, data, single=single, chk_last_weeks=53 if single else 1)
                all_signals[symbol] = result
                completed_count = len(all_signals)
                total_count = len(tickers)
                completion_percent = int((completed_count / total_count) * 100)
                if completion_percent in {5, 25, 50, 75}:
                    current_doc = get_document("process-list", process_id)
                    if current_doc.get("completionPercent") != completion_percent:
                        update_document("process-list", process_id, {
                            "completionPercent": completion_percent,
                            "completionStatus": f"In progress {completed_count}/{total_count}"
                        })
                        print(f"Progress: {completion_percent}% ({completed_count}/{total_count}), Process ID: {process_id}")
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        filtered_signals = {symbol: result for symbol, result in all_signals.items() if result and result != []}

        # Update Firestore with completion status and result
        update_content = {
            "completionPercent": 100,
            "completionStatus": "Backtest completed",
            "result": filtered_signals
        }

        process_list_collection = "process-list"
        update_document(process_list_collection, process_id, update_content)
        print(f"Backtest completed for all symbols. Process ID: {process_id}")
        
    except Exception as e:
        print(f"Error in async_backtest: {e}")
        update_document("process-list", process_id, {
            "completionStatus": f"Error: {str(e)}"
        })


def run_backtests(segment: str, single: bool = False):
    """
    Run backtests for a given segment and return the process ID.
    """
   
    
    process_id = get_process_id(segment)
    threading.Thread(target=async_backtest, args=(segment, process_id, single)).start()
    
    return process_id

def get_process_id(segment):
    process_id = str(uuid.uuid4())
    # Update Firestore with initial status
    create_document("process-list", process_id, {
        "completionPercent": 0,
        "completionStatus": "Backtest started",
        "processId": process_id,
        "segment_or_symbol": segment,
        "startTime": datetime.datetime.now().isoformat(),
        "result": {}
    })
    
    return process_id

def get_backtest_status(process_id):
    data = get_document("process-list", process_id)
    if data is None:
        return None
    
    return {
        "completionPercent": data.get("completionPercent"),
        "completionStatus": data.get("completionStatus"),
        "processId": data.get("processId"),
        "segment_or_symbol": data.get("segment_or_symbol"),
        "startTime": data.get("startTime"),
        "result": data.get("result")
    }
    

# Load tickers from a file
def load_tickers(file_path):
    with open(file_path, "r") as file:
        tickers = [line.strip() for line in file.readlines()]
    return tickers

# Run Backtest for Reliance Industries (NSE)
if __name__ == "__main__":
    process_id = get_process_id("JSWSTEEL.NS")   
    async_backtest("JSWSTEEL.NS", process_id, single=True) 
    print(f"Process ID: {process_id}")
