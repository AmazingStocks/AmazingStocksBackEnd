import backtrader as bt
from .BaseStrategy import BaseStrategy  # new import

class MovingAverageCrossoverStrategy(BaseStrategy):  # changed inheritance
    params = (
        ("short_period", 50),
        ("long_period", 200),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Short and Long Moving Averages
        self.sma_short = bt.indicators.SimpleMovingAverage(period=self.params.short_period)
        self.sma_long = bt.indicators.SimpleMovingAverage(period=self.params.long_period)

    def next(self):
        if self.position:
            # Exit condition: Short MA crosses below Long MA
            if self.sma_short[0] < self.sma_long[0]:
                self.close()
                self.log(f"SELL: {self.data.datetime.date(0)} | Price: {self.data.close[0]}")
        else:
            # Buy condition: Short MA crosses above Long MA
            if self.sma_short[0] > self.sma_long[0]:
                self.buy()
                self.log(f"BUY: {self.data.datetime.date(0)} | Price: {self.data.close[0]}")
