import backtrader as bt


class TradeSignalsAnalyzer(bt.Analyzer):
    def start(self):
        self.signals = []
    
    def get_analysis(self):
        
        last_signals = getattr(self.strategy, 'last_signals', None)
        return last_signals