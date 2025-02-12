import backtrader as bt

class MovingAverageCrossoverStrategy(bt.Strategy):
    params = (
        ("short_period", 20),
        ("long_period", 100),
    )

    def __init__(self):
        # Short and Long Moving Averages
        self.sma_short = bt.indicators.SimpleMovingAverage(period=self.params.short_period)
        self.sma_long = bt.indicators.SimpleMovingAverage(period=self.params.long_period)

    def next(self):
        if self.position:
            # Exit condition: Short MA crosses below Long MA
            if self.sma_short[0] < self.sma_long[0]:
                self.close()
                print(f"SELL: {self.data.datetime.date(0)} | Price: {self.data.close[0]}")
        else:
            # Buy condition: Short MA crosses above Long MA
            if self.sma_short[0] > self.sma_long[0]:
                self.buy()
                print(f"BUY: {self.data.datetime.date(0)} | Price: {self.data.close[0]}")
