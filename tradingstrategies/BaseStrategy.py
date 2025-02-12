import backtrader as bt

class BaseStrategy(bt.Strategy):
    def __init__(self, *args, **kwargs):
        pass
    
    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f"{dt} {txt}")
    # ...common methods can be added here...