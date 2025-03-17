import backtrader as bt
import datetime as dt

class BaseStrategy(bt.Strategy):
    def __init__(self, *args, **kwargs):
        self.chk_last_weeks = kwargs.get("chk_last_weeks", 999)
        self.symbol = kwargs.get("symbol", "TCS.NS")
        self.print_signals = kwargs.get("print_signals", False)
        # List to store signals as tuples: (date, signal type, price)
        self.generated_signals = []
        
    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f"{dt} {txt}")
        
    def close(self, data=None, size=None, **kwargs):  
        # Get the current bar's date (converted to a Python date)
        current_date = self.data.datetime.date(0)      
        signal = {
            "date": str(current_date),
            "signal_type": "SELL",
            "price": self.data.close[0]
        }
        self.generated_signals.append(signal)
        return super().close(data, size, **kwargs)
    
    def buy(self, data=None, size=None, price=None, plimit=None, exectype=None, 
            valid=None, tradeid=0, oco=None, trailamount=None, trailpercent=None, 
            parent=None, transmit=True, **kwargs):
        # Get the current bar's date (converted to a Python date)
        current_date = self.data.datetime.date(0)
        signal = {
            "date": str(current_date),
            "signal_type": "BUY",
            "price": self.data.close[0]
        }
        self.generated_signals.append(signal)
        return super().buy(data, size, price, plimit, exectype, valid, tradeid, oco, trailamount, trailpercent, parent, transmit, **kwargs)
    
    def stop(self):
        # When the strategy ends, determine the last date in the data feed
        last_date = self.data.datetime.date(0)
        # Define the cutoff date as one week before the last date
        cutoff_date = last_date - dt.timedelta(weeks=self.chk_last_weeks)
        if self.generated_signals:            
            self.last_signals = [signal for signal in self.generated_signals if dt.datetime.strptime(signal["date"], '%Y-%m-%d').date() >= cutoff_date]
        # New feature: print all trade signals if enabled
        if self.print_signals:
            for signal in self.generated_signals:
                self.log(f"Trade Signal: {signal}")

