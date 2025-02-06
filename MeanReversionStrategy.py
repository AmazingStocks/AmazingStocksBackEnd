# Define Trading Strategy
import backtrader as bt


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