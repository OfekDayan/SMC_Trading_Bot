import pandas
import plotly.graph_objects as go
from Models.candle import Candle
from tools.fibonacci_retracement import FibonacciRetracement
from tools.order_block import OrderBlock
from tools.point import Point


class DecisionManager:
    def __init__(self, order_block: OrderBlock, pullback_zone_df: pandas.DataFrame):
        self.order_block = order_block
        self.pullback_zone_df = pullback_zone_df

    def get_signal_price_level(self):
        WANTED_FIBO_LEVEL = 90

        if self.order_block.is_bullish:
            swing_start = self.order_block.get_top_left()

            end_time = self.pullback_zone_df.index[-1]
            price = self.pullback_zone_df.iloc[0]['High']
            swing_end = Point(end_time, price)
        else:
            swing_start = self.order_block.bottom_left

            end_time = self.pullback_zone_df.index[-1]
            price = self.pullback_zone_df.iloc[0]['Low']
            swing_end = Point(end_time, price)

        fibonacci_retracement = FibonacciRetracement(swing_start, swing_end)
        fibo_level = fibonacci_retracement.get_level_price(WANTED_FIBO_LEVEL)
        return fibo_level

    def get_signal_point(self, chart: go.Figure = None):
        price_to_send_signal = self.get_signal_price_level()
        # fibonacci_retracement.plot(chart, price_to_send_signal.datetime)

        # Find the time of the candle touched the "signal level"
        for candle_time, row in self.pullback_zone_df.iterrows():
            candle = Candle(candle_time, row)

            if (self.order_block.is_bullish and candle.low_price <= price_to_send_signal) or \
                    (not self.order_block.is_bullish and candle.high_price >= price_to_send_signal):
                signal_point = Point(candle_time, price_to_send_signal)

                if chart:
                    signal_point.plot(chart, 'Orange', 10)

                return signal_point

        return None

    def is_to_send_signal(self):
        if self.order_block.is_failed or self.order_block.is_touched:
            return False

        signal_point = self.get_signal_point()

        if signal_point is None:
            return False

        # Get the current (last) candle
        # last_candle_row = self.pullback_zone_df.iloc[-1]
        last_candle_datetime = self.pullback_zone_df.index[-1]
        # last_candle = Candle(last_candle_datetime, last_candle_row)
        return signal_point.datetime == last_candle_datetime