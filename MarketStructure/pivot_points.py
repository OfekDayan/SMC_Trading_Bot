import pandas
from Models.candle import Candle
import plotly.graph_objects as go
from MarketStructure.retracement_verifier import RetracementVerifier
from tools.horizontal_trend_line import HorizontalTrendLine
from tools.point import Point


class PivotPoints:
    def __init__(self, df: pandas.DataFrame):
        self.df = df
        self.temp_df = df
        self.__trend = None
        self.current_candle_index = 0
        self.retracement_verifier = RetracementVerifier()
        self.low = None
        self.high = None
        self.dynamic_low = None
        self.dynamic_high = None
        self.choches_and_boses = []
        self.market_structure_points = []

    def __find_trend(self):
        self.current_candle_index += 0
        self.low = None
        self.high = None
        self.dynamic_low = None
        self.dynamic_high = None

        max_high_value = self.df['High'].idxmax()
        min_low_value = self.df['Low'].idxmin()

        if max_high_value < min_low_value:
            self.__trend = 'downtrend'
            self.temp_df = self.temp_df.loc[max_high_value:]
            first_row = self.temp_df.iloc[0]

            self.high = Point(first_row.name, first_row['High'])
            self.dynamic_low = Point(first_row.name, first_row['Low'])

        else:
            self.__trend = 'uptrend'
            self.temp_df = self.temp_df.loc[min_low_value:]
            first_row = self.temp_df.iloc[0]

            self.low = Point(first_row.name, first_row['Low'])
            self.dynamic_high = Point(first_row.name, first_row['High'])

    def find(self):
        self.__find_trend()
        rows_number = len(self.temp_df.index)

        while self.current_candle_index < rows_number:
            if self.__trend == 'downtrend':
                self.downtrend()
            else:
                self.uptrend()

    def add_to_chart(self, figure: go.Figure):
        self.plot_smc_levels(figure)
        self.plot_pivot_points(figure)

    def plot_pivot_points(self, figure: go.Figure):
        for point in self.market_structure_points:
            point.plot(figure, 'black')

    def plot_smc_levels(self, figure: go.Figure):
        for choch_bos in self.choches_and_boses:
            color = 'red' if choch_bos.name == 'CHoCH' else 'blue'
            choch_bos.plot(figure, color)

    def uptrend(self):
        for index, row in self.temp_df[self.current_candle_index:].iterrows():
            candle = Candle(index, row)
            self.current_candle_index += 1

            if self.low is not None and self.high is not None:
                # LL found
                if candle.close_price < self.low.price:
                    self.choches_and_boses.append(HorizontalTrendLine('CHoCH', self.low.datetime, candle.time, self.low.price))
                    self.low = None
                    self.dynamic_low = Point(candle.time, candle.low_price)
                    self.__trend = 'downtrend'
                    return

                # HL found
                if candle.close_price > self.high.price:
                    self.choches_and_boses.append(HorizontalTrendLine('BOS', self.high.datetime, candle.time, self.high.price))

                    self.low = Point(self.dynamic_low.datetime, self.dynamic_low.price)
                    self.market_structure_points.append(Point(self.low.datetime, self.low.price, 'HL'))

                    self.dynamic_high = Point(candle.time, candle.high_price)
                    self.high = None
                    continue

            if candle.high_price > self.dynamic_high.price:
                self.dynamic_high = Point(candle.time, candle.high_price)

                if self.high is None or self.dynamic_high.price < self.high.price:
                    self.dynamic_low = Point(candle.time, candle.low_price)

                continue

            # Move down dynamic low
            if self.dynamic_low is None or candle.low_price < self.dynamic_low.price:
                self.dynamic_low = Point(candle.time, candle.low_price)

            if self.high is None:
                swing_start = self.low
                swing_end = self.dynamic_high
                retracement_level = self.dynamic_low

                if self.retracement_verifier.is_valid(self.temp_df, swing_start, swing_end, retracement_level):
                    self.high = Point(self.dynamic_high.datetime, self.dynamic_high.price)
                    self.market_structure_points.append(Point(self.high.datetime, self.high.price, 'HH'))

    def downtrend(self):
        for index, row in self.temp_df[self.current_candle_index:].iterrows():
            candle = Candle(index, row)
            self.current_candle_index += 1

            if self.low is not None and self.high is not None:
                # HH found
                if candle.close_price > self.high.price:
                    self.choches_and_boses.append(HorizontalTrendLine('CHoCH', self.high.datetime, candle.time, self.high.price))
                    self.high = None
                    self.dynamic_high = Point(candle.time, candle.high_price)
                    self.__trend = 'uptrend'
                    return

                # LH found
                if candle.close_price < self.low.price:
                    self.choches_and_boses.append(HorizontalTrendLine('BOS', self.low.datetime, candle.time, self.low.price))

                    self.high = Point(self.dynamic_high.datetime, self.dynamic_high.price)
                    self.market_structure_points.append(Point(self.high.datetime, self.high.price, 'LH'))

                    self.dynamic_low = Point(candle.time, candle.low_price)
                    self.low = None
                    continue

            if candle.low_price < self.dynamic_low.price:
                self.dynamic_low = Point(candle.time, candle.low_price)

                if self.low is None or self.dynamic_low.price > self.low.price:
                    self.dynamic_high = Point(candle.time, candle.high_price)

                continue

            # Move up dynamic up
            if self.dynamic_high is None or candle.high_price > self.dynamic_high.price:
                self.dynamic_high = Point(candle.time, candle.high_price)

            # LL
            if self.low is None:
                swing_start = self.high
                swing_end = self.dynamic_low
                retracement_level = self.dynamic_high

                if self.retracement_verifier.is_valid(self.temp_df, swing_start, swing_end, retracement_level):
                    self.low = Point(self.dynamic_low.datetime, self.dynamic_low.price)
                    self.market_structure_points.append(Point(self.low.datetime, self.low.price, 'LL'))
