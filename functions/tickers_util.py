from yahoo_fin import stock_info as si


def load_tickers(file_path):
    with open(file_path, "r") as file:
        tickers = [line.strip() for line in file.readlines()]
    return tickers


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