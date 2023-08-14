import pandas
from Models.candle import Candle
import plotly.graph_objects as go
import talib


class ChartMethods:
    def __init__(self, df: pandas.DataFrame):
        self.df = df

    def calculate(self, figure: go.Figure = None):
        self.calculate_candles_patterns()
        self.calculate_imbalances(figure)

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

    def calculate_candles_patterns(self):
        self.__apply_candle('Marubozu', talib.CDLMARUBOZU)
        self.__apply_candle('Engulfing', talib.stream_CDLENGULFING)

        self.__apply_candle('Doji', talib.CDLDOJI)
        self.__apply_candle('Doji_star', talib.stream_CDLDOJISTAR)
        self.__apply_candle('Dragonfly_doji', talib.CDLDRAGONFLYDOJI)
        self.__apply_candle('Gravestone_doji', talib.stream_CDLGRAVESTONEDOJI)
        self.__apply_candle('Long_legged_doji', talib.stream_CDLLONGLEGGEDDOJI)

        self.__apply_candle('Hammer', talib.CDLHAMMER)
        self.__apply_candle('Inverted_hammer', talib.stream_CDLINVERTEDHAMMER)
        self.__apply_candle('Spinning_top', talib.stream_CDLSPINNINGTOP)
        self.__apply_candle('Hanging_man', talib.CDLHANGINGMAN)
        self.__apply_candle('Shooting_star', talib.stream_CDLSHOOTINGSTAR)
        self.__apply_candle('Morning_tar', talib.CDLMORNINGSTAR)
        self.__apply_candle('Dark_cloud_cover', talib.CDLDARKCLOUDCOVER)
        self.__apply_candle('Evening_star', talib.CDLEVENINGSTAR)
        self.__apply_candle('Piercing_line', talib.CDLPIERCING)

    def calculate_rsi(self):
        pass

    def calculate_rsi_divergence(self):
        pass

    def __apply_candle(self, name: str, func):
        self.df[name] = func(self.df['Open'], self.df['High'], self.df['Low'], self.df['Close'])
        self.df[name] = self.df.apply(lambda x: True if x[name] == 100 or x[name] == -100 else False, axis=1)
