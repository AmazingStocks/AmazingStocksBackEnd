import re
import yfinance as yf
import time

from firebase_admin import initialize_app, credentials, firestore
import pandas as pd
from firebase_admin import get_app

try:
    get_app()
except ValueError:
    cred = credentials.Certificate("serviceAccountKey.json")
    initialize_app(cred)
    
db = firestore.client()

def get_timedelta_from_period(period: str):
    """
    Converts a period string to a pandas Timedelta.
    
    Supported formats:
      - "Nd" for days
      - "Nw" for weeks
      - "Nm" for months (approximated as 30 days per month)
      - "Ny" for years (approximated as 365 days per year)
    
    Args:
        period (str): Period string
        
    Returns:
        pandas.Timedelta: The corresponding Timedelta.
        
    Raises:
        ValueError: If period is in an unsupported format.
    """
    match = re.match(r"(\d+)([dwmy])", period.lower())
    if not match:
        raise ValueError(f"Unsupported period format: {period}")
    amount, unit = match.groups()
    amount = int(amount)
    if unit == "d":
        return pd.Timedelta(days=amount)
    elif unit == "w":
        return pd.Timedelta(weeks=amount)
    elif unit == "m":
        return pd.Timedelta(days=amount * 30)
    elif unit == "y":
        return pd.Timedelta(days=amount * 365)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")

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
    # Firestore batch limit is 500 writes per batch. Write in chunks.
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

    # commit any leftovers
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
        # If data exists, download data from the day after the last available date to today.
        start_date = (last_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        # If no data exists, download the last 1 year of data.
        start_date = (pd.Timestamp.today() - pd.Timedelta(days=365)).strftime('%Y-%m-%d')
    
    end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    
    # Check if there are any business days between start_date and end_date
    # If no business days, skip the download.
    # Note: This is a naive approach and may not account for holidays.
    # You may want to use a library like `pandas_market_calendars` for more accurate business day calculations.
    # For simplicity, we will use the default business day calendar.
    business_days = pd.bdate_range(start=start_date, end=end_date)
    if len(business_days) == 0:
        print("No working days found between start_date and end_date. Skipping download.")
        return
    
    # Fetch data from Yahoo Finance
    data = get_data(symbol, start=start_date, end=end_date, interval="1d")
    
    if not data.empty:
        save_to_firestore(data, symbol)
        print(f"Data for {symbol} saved to Firestore.")
    else:
        print(f"No new data to save for {symbol}.")

def get_data_from_firestore(symbol, dwnld_frm_yf=False, period="1y"):
    """
    Fetches historical data for a given stock symbol from Firestore and returns it as a
    DataFrame in the same format as yfinance.download (Date as index with columns: open, high, low, close, volume).
    The data is filtered to retain only records within the specified period relative to today.
    
    Additionally, if the stored data is not updated until the last working day, it calls yf_to_firestore to
    update Firestore.
    
    Args:
        symbol (str): The stock symbol to fetch data for.
        period (str): Period as a string (e.g., '1y', '6mo', '30d') to filter the data.
        
    Returns:
        pandas.DataFrame: DataFrame containing the filtered historical data.
    """
    collection_ref = db.collection("stocks").document(symbol).collection("daily")
    docs = collection_ref.stream()
    
    records = []
    for doc in docs:
        records.append(doc.to_dict())
    
    df = pd.DataFrame(records)

    if dwnld_frm_yf:
        # If no data exists in Firestore, update Firestore.
        if df.empty:
            yf_to_firestore(symbol)
            docs = collection_ref.stream()
            records = [doc.to_dict() for doc in docs]
            df = pd.DataFrame(records)
            if df.empty:
                return df

        # Convert 'Date' back to datetime and set as index.
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        # Determine the last working day using business day offset.
        last_working_day = (pd.Timestamp.today() - pd.tseries.offsets.BDay(1)).normalize()
        if df.index.max() < last_working_day:
            print("Data not available until last working day. Updating Firestore data...")
            yf_to_firestore(symbol)
            docs = collection_ref.stream()
            records = [doc.to_dict() for doc in docs]
            df = pd.DataFrame(records)
            if df.empty:
                return df
            
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df.sort_index(inplace=True)
        
    # Ensure the DataFrame has the same columns as yfinance returns.
    desired_columns = ["open", "high", "low", "close", "volume"]
    df = df.reindex(columns=desired_columns)
    
    # Filter data based on the specified period.
    try:
        delta = get_timedelta_from_period(period)
    except ValueError as e:
        print(f"Error parsing period: {e}")
        return df
    threshold_date = pd.Timestamp.today() - delta
    df = df[df.index >= threshold_date]
    
    return df

if __name__ == "__main__":
    
    # Example usage
    symbol = "ADANIENT.NS"
    yf_to_firestore(symbol)
    data = get_data_from_firestore(symbol, period="1y")
    print(data.head())