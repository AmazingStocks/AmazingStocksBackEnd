import backtrader as bt
from sklearn.neighbors import KNeighborsClassifier
import numpy as np

class KNNMovingAverageCrossoverStrategy(bt.Strategy):
    params = (
        ("short_period", 50),
        ("long_period", 200),
        ("n_neighbors", 5),
    )

    def __init__(self):
        # Short and Long Moving Averages
        self.sma_short = bt.indicators.SimpleMovingAverage(period=self.params.short_period)
        self.sma_long = bt.indicators.SimpleMovingAverage(period=self.params.long_period)
        # KNN Classifier
        self.knn = KNeighborsClassifier(n_neighbors=self.params.n_neighbors)
        self.data_points = []

    def next(self):
        # Collect data points for KNN
        self.data_points.append([self.data.close[0], self.sma_short[0], self.sma_long[0]])
        if len(self.data_points) > self.params.long_period:
            X = np.array(self.data_points[-self.params.long_period:])
            y = np.sign(np.diff(X[:, 0]))  # Target: price movement direction
            self.knn.fit(X[:-1], y)  # Train KNN

            prediction = self.knn.predict([X[-1]])  # Predict next movement

            if self.position:
                # Exit condition: Short MA crosses below Long MA or KNN predicts downward movement
                if self.sma_short[0] < self.sma_long[0] or prediction < 0:
                    self.close()
                    print(f"SELL: {self.data.datetime.date(0)} | Price: {self.data.close[0]}")
            else:
                # Buy condition: Short MA crosses above Long MA or KNN predicts upward movement
                if self.sma_short[0] > self.sma_long[0] or prediction > 0:
                    self.buy()
                    print(f"BUY: {self.data.datetime.date(0)} | Price: {self.data.close[0]}")
