import backtrader as bt
import yfinance as yf
import datetime
import matplotlib
import time
import json
import uuid

from firestore_util import create_document, update_document, get_collection, get_document, delete_document


from TradeSignalsAnalyzer import TradeSignalsAnalyzer
from timer_util import timeit
from tickers_util import get_all_tickers
from tradingstrategies.MeanReversionStrategy import MeanReversionStrategy
from tradingstrategies.MovingAverageCrossoverStrategy import MovingAverageCrossoverStrategy
import psutil
matplotlib.use("Agg")  # Use Agg backend for non-GUI environments
import matplotlib.pyplot as plt

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
@timeit
def backtest(symbol, chk_last_weeks=1):
    """
    Backtest function to run the Moving Average Crossover strategy.
    """     
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MovingAverageCrossoverStrategy, chk_last_weeks=chk_last_weeks, symbol=symbol)
    
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


def async_backtest(segment: str, process_id, single: bool = False):
    """
    Asynchronous backtest function to run in a separate thread.
    """
    if single:
        tickers = [segment]
    else:
        tickers = get_all_tickers(segment)
    print(f"Running backtest for {len(tickers)} symbols in segment: {segment}")    
    try:
        all_signals = {}
        total_count = len(tickers)
        print(f"Total symbols to process: {total_count}")
        for symbol in tickers:
            print(f"Processing symbol: {symbol}")
            try:
                result = backtest(symbol, chk_last_weeks=53 if single else 1)
                print(f"Backtest complete for {symbol}")
                process = psutil.Process()
                mem_usage_mb = process.memory_info().rss / (1024 * 1024)
                print(f"Memory utilization: {mem_usage_mb:.2f} MB")
                # Save the result to Firestore
                all_signals[symbol] = result
                completed_count = len(all_signals)
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
        
        print(f"Progress: {100}% ({completed_count}/{total_count}), Process ID: {process_id}")

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
   
    
    process_id = get_process_id(segment, single)
    
    return process_id

def get_process_id(segment, single: bool = False):
    process_id = str(uuid.uuid4())
    # Update Firestore with initial status
    create_document("process-list", process_id, {
        "completionPercent": 0,
        "completionStatus": "Backtest started",
        "processId": process_id,
        "segment_or_symbol": segment,
        "startTime": datetime.datetime.now().isoformat(),
        "single": single,
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
# Run Backtest for Reliance Industries (NSE)
if __name__ == "__main__":
    process_id = get_process_id("JSWSTEEL.NS")   
    async_backtest("JSWSTEEL.NS", process_id, single=True) 
    print(f"Process ID: {process_id}")
