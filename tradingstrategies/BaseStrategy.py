import backtrader as bt
import datetime as dt

class BaseStrategy(bt.Strategy):
    def __init__(self, *args, **kwargs):
        self.chk_last_weeks = kwargs.get("chk_last_weeks", 999)
        self.symbol = kwargs.get("symbol", "TCS.NS")
        # List to store signals as tuples: (date, signal type, price)
        self.signals = []
    
    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f"{dt} {txt}")
        
    def close(self, data=None, size=None, **kwargs):  
        # Get the current bar's date (converted to a Python date)
        current_date = self.data.datetime.date(0)      
        self.signals.append((current_date, 'SELL', self.data.close[0]))
        return super().close(data, size, **kwargs)
    
    def buy(self, data=None, size=None, price=None, plimit=None, exectype=None, 
            valid=None, tradeid=0, oco=None, trailamount=None, trailpercent=None, 
            parent=None, transmit=True, **kwargs):
        # Get the current bar's date (converted to a Python date)
        current_date = self.data.datetime.date(0)
        self.signals.append((current_date, 'BUY', self.data.close[0]))
        return super().buy(data, size, price, plimit, exectype, valid, tradeid, oco, trailamount, trailpercent, parent, transmit, **kwargs)
    
    def stop(self):
        # When the strategy ends, determine the last date in the data feed
        last_date = self.data.datetime.date(0)
        # Define the cutoff date as one week before the last date
        cutoff_date = last_date - dt.timedelta(weeks=self.chk_last_weeks)
        if self.signals:            
            last_signals = [signal for signal in self.signals if signal[0] >= cutoff_date]
            if last_signals:
                print(f"@@@@@@@  {self.symbol} @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
                print(f"\nSignals in the last {self.chk_last_weeks} week:")
                for signal in last_signals:
                    signal_date, signal_type, price = signal
                    print(f"Date: {signal_date}, Signal: {signal_type}, Price: {price}")
        