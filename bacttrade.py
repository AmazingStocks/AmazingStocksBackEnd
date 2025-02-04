import backtrader as bt
import yfinance as yf
import datetime
import matplotlib
matplotlib.use("Agg")  # Use Agg backend for non-GUI environments

# Define Trading Strategy
class MeanReversionStrategy(bt.Strategy):
    params = (
        ("boll_period", 20),
        ("rsi_period", 14),
        ("rsi_lower", 30),
        ("rsi_upper", 70),
    )

    def __init__(self):
        # Bollinger Bands
        self.bb = bt.indicators.BollingerBands(period=self.params.boll_period)
        # RSI Indicator
        self.rsi = bt.indicators.RSI(period=self.params.rsi_period)

    def next(self):
        if self.position:
            # Exit conditions: Price returns to the mean (SMA20)
            if self.data.close[0] > self.bb.lines.mid[0]:
                self.close()
                print(f"SELL: {self.data.datetime.date(0)} | Price: {self.data.close[0]}")

        else:
            # Buy when price touches lower Bollinger Band & RSI < 30
            if self.data.close[0] <= self.bb.lines.bot[0] and self.rsi[0] < self.params.rsi_lower:
                self.buy()
                print(f"BUY: {self.data.datetime.date(0)} | Price: {self.data.close[0]}")

# Download Historical Data from Yahoo Finance
def get_data(symbol, start="2023-01-01", end="2024-01-01"):
    data = yf.download(symbol, start=start, end=end, multi_level_index=False)
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
    cerebro.addstrategy(MeanReversionStrategy)

    # Load Data
    df = get_data(symbol)
    data = bt.feeds.PandasData(dataname=df)

    # Add data to Cerebro
    cerebro.adddata(data)
    cerebro.broker.set_cash(100000)  # Set initial capital
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  # Number of shares per trade

    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")

    # Save the plot as an image file instead of displaying it
    fig = cerebro.plot(style='candlestick')[0][0]
    fig.savefig("backtest_plot.png")  # Save as PNG file

# Run Backtest for Reliance Industries (NSE)
if __name__ == "__main__":
    backtest("RELIANCE.NS")
