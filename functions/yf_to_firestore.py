import yfinance as yf
import time

from firebase_admin import  firestore
import pandas as pd

db = firestore.client()

def get_data(symbol, period="1y", interval="1d"):
    
    for attempt in range(5):
        try:
            data = yf.download(symbol, period=period, interval=interval, multi_level_index=False,progress=False)
            data = data.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            })
            break
        except yf.shared._exceptions.YFRateLimitError:
            wait = 2 ** attempt
            print(f"Rate-limited; sleeping {wait}s")
            time.sleep(wait)
    
    return data

def save_to_firestore(data, symbol):
    data.reset_index(inplace=True)
    data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
    records = data.to_dict(orient="records")      # list[dict]
    batch = db.batch()
    for i, row in enumerate(records, 1):
        doc = (
            db.collection("stocks")
            .document(symbol)
            .collection("daily")
            .document(row["Date"])
        )
        batch.set(doc, row)
        if i % 500 == 0:
            batch.commit()
            batch = db.batch()       # start fresh

    # commit leftovers
    batch.commit()
    
def yf_to_firestore(symbol):
    """
    Fetches historical data for a given stock symbol from Yahoo Finance and saves it to Firestore.
    
    Args:
        symbol (str): The stock symbol to fetch data for.
    """
    data = get_data(symbol)
    save_to_firestore(data, symbol)
    print(f"Data for {symbol} saved to Firestore.")
    
    
def get_data_from_firestore(symbol):
    """
    Fetches historical data for a given stock symbol from Firestore and returns it as a
    DataFrame in the same format as yfinance.download (Date as index and columns: open, high, low, close, volume).
    
    Args:
        symbol (str): The stock symbol to fetch data for.
        
    Returns:
        pandas.DataFrame: DataFrame containing the historical data.
    """

    collection_ref = db.collection("stocks").document(symbol).collection("daily")
    docs = collection_ref.stream()
    
    records = []
    for doc in docs:
        records.append(doc.to_dict())
    
    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Convert 'Date' back to datetime and set as index
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df.sort_index(inplace=True)
    
    # Ensure the DataFrame has the same columns as yfinance returns
    desired_columns = ["open", "high", "low", "close", "volume"]
    df = df.reindex(columns=desired_columns)
    
    return df