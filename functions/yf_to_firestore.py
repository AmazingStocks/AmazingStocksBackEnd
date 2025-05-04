import yfinance as yf
import time

from firebase_admin import  initialize_app,  credentials, firestore
import pandas as pd
from firebase_admin import get_app

try:
    get_app()
except ValueError:
    cred = credentials.Certificate("serviceAccountKey.json")
    initialize_app(cred)
    
db = firestore.client()

def get_data(symbol, start=None, end=None, interval="1d"):
    """
    Fetches historical data for a given stock symbol from Yahoo Finance.
    
    Args:
        symbol (str): The stock symbol to fetch data for.
        start (str): The start date in 'YYYY-MM-DD' format.
        end (str): The end date in 'YYYY-MM-DD' format.
        interval (str): The data interval (e.g., '1d', '1wk', '1mo').
    
    Returns:
        pandas.DataFrame: DataFrame containing the historical data.
    """
    for attempt in range(5):
        try:
            data = yf.download(symbol, start=start, end=end, interval=interval, multi_level_index=False, progress=False)
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
    print(f"Saving {len(records)} records to Firestore for {symbol}...")
    # Create a batch to write data in chunks
    # Firestore has a limit of 500 writes per batch
    # so we will write in chunks of 500
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
    # Check the last available date in Firestore
    collection_ref = db.collection("stocks").document(symbol).collection("daily")
    docs = collection_ref.order_by("Date", direction=firestore.Query.DESCENDING).limit(1).stream()
    
    last_date = None
    for doc in docs:
        last_date = pd.to_datetime(doc.to_dict().get("Date"))
        break  # Only need the first document
    
    if last_date:
        # If data exists, download data from the day after the last available date to today
        start_date = (last_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        # If no data exists, download the last 1 year of data
        start_date = (pd.Timestamp.today() - pd.Timedelta(days=365)).strftime('%Y-%m-%d')
    
    end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    
    # Fetch data from Yahoo Finance
    data = get_data(symbol, start=start_date, end=end_date, interval="1d")
    
    if not data.empty:
        save_to_firestore(data, symbol)
        print(f"Data for {symbol} saved to Firestore.")
    else:
        print(f"No new data to save for {symbol}.")
    
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

if __name__ == "__main__":
    
    # Example usage
    symbol = "ADANIENT.NS"
    yf_to_firestore(symbol)
    data = get_data_from_firestore(symbol)
    print(data.head())