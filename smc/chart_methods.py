import pandas
from Models.candle import Candle
import plotly.graph_objects as go
import talib


class ChartMethods:
    def __init__(self, df: pandas.DataFrame):
        self.df = df

    def calculate_imbalances(self, figure: go.Figure = None):
        self.df['Imbalance'] = 0

        self.df.loc[self.df['Close'] > self.df['Open'], 'Imbalance'] = self.df['Low'].shift(-1) - self.df['High'].shift(
            1)
        self.df.loc[self.df['Close'] > self.df['Open'], 'Imbalance_Start'] = self.df['Low'].shift(-1)
        self.df.loc[self.df['Close'] > self.df['Open'], 'Imbalance_End'] = self.df['High'].shift(1)

        self.df.loc[self.df['Open'] > self.df['Close'], 'Imbalance'] = self.df['Low'].shift(1) - self.df['High'].shift(
            -1)
        self.df.loc[self.df['Open'] > self.df['Close'], 'Imbalance_Start'] = self.df['High'].shift(-1)
        self.df.loc[self.df['Open'] > self.df['Close'], 'Imbalance_End'] = self.df['Low'].shift(1)

        # Set to 0 negative imbalances
        self.df.loc[self.df['Imbalance'] < 0, 'Imbalance'] = 0

        # Set values less than the average to 0 in the "Imbalance" column
        positive_imbalances_df = self.df[self.df['Imbalance'] > 0]
        average_imbalance = positive_imbalances_df['Imbalance'].mean()
        self.df.loc[self.df['Imbalance'] < average_imbalance * 2, 'Imbalance'] = 0

        # add to chart
        if figure:
            for index, row in self.df[1:].iterrows():
                candle = Candle(index, row)
                candle.plot_imbalance(figure)

                # TODO: remove me!
                # candle.plot_type(figure)

    def calculate_big_candles(self):
        self.df['body_size'] = abs(self.df['Open'] - self.df['Close'])
        average_body_size = self.df['body_size'].mean()

        # Create a new column 'body_size' with True for values >= 2 * average, False otherwise
        self.df['is_big_candle'] = self.df['body_size'] >= 2 * average_body_size
        self.df = self.df.drop(columns=['body_size'])

    def calculate_candles_patterns(self):
        patterns_to_apply = [
            'CDLMARUBOZU', 'CDLENGULFING', 'CDLDOJI', 'CDLDOJISTAR', 'CDLDRAGONFLYDOJI',
            'CDLGRAVESTONEDOJI', 'CDLLONGLEGGEDDOJI', 'CDLHAMMER', 'CDLINVERTEDHAMMER',
            'CDLSPINNINGTOP', 'CDLHANGINGMAN', 'CDLSHOOTINGSTAR', 'CDLMORNINGSTAR',
            'CDLDARKCLOUDCOVER', 'CDLEVENINGSTAR', 'CDLPIERCING'
        ]

        for pattern_name in patterns_to_apply:
            self.__apply_candle(pattern_name, getattr(talib, pattern_name))

    def __apply_candle(self, name: str, func):
        pattern_results = func(self.df['Open'], self.df['High'], self.df['Low'], self.df['Close'])
        self.df[name] = (pattern_results == 100) | (pattern_results == -100)
