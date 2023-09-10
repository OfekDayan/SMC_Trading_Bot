import pandas
import plotly.graph_objects as go
from Models.candle import Candle
from tools.fibonacci_retracement import FibonacciRetracement
from tools.order_block import OrderBlock, OrderBlockStatus
from tools.point import Point


class SignalDetector:
    def __init__(self, order_block: OrderBlock, pullback_zone_df: pandas.DataFrame, timeframe):
        self.order_block = order_block
        self.pullback_zone_df = pullback_zone_df
        self.timeframe = timeframe

    def get_price_by_fib_level(self, fibo_level) -> float:
        # Find swing start and end
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

        # Get fibo level price
        fibonacci_retracement = FibonacciRetracement(swing_start, swing_end)
        fibo_level_price = fibonacci_retracement.get_level_price(fibo_level)
        return fibo_level_price

    def get_signal_price_level(self) -> float:
        WANTED_FIBO_LEVEL = 80
        return self.get_price_by_fib_level(WANTED_FIBO_LEVEL)

    def get_signal_point(self) -> Point:
        # Get the price threshold to send signal
        price_to_send_signal = self.get_signal_price_level()

        # Find the time of the candle touched the "signal level"
        for candle_time, row in self.pullback_zone_df.iterrows():
            candle = Candle(candle_time, row, self.timeframe)

            if (self.order_block.is_bullish and candle.low_price <= price_to_send_signal) or \
                    (not self.order_block.is_bullish and candle.high_price >= price_to_send_signal):
                signal_point = Point(candle.time, price_to_send_signal)
                return signal_point

        return None

    def is_last_candle_reached_signal_price(self, chart: go.Figure = None) -> bool:
        signal_point = self.get_signal_point()

        if signal_point is None:
            return False

        # Get the last candle
        last_candle_datetime = self.pullback_zone_df.index[-1]
        is_to_send_signal = signal_point.datetime == last_candle_datetime

        if chart:
            signal_point.plot(chart, 'Orange', 10)

        return is_to_send_signal
