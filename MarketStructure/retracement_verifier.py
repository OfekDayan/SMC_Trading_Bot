import pandas
from MarketStructure.candles_counter import is_n_non_indecision_candles, is_n_candles
from tools.fibonacci_retracement import FibonacciRetracement
from tools.point import Point


class RetracementVerifier:

    def is_valid(self, df: pandas.DataFrame, swing_start: Point, swing_end: Point, retracement: Point):
        if df.empty:
            return False

        fibonacci_retracement = FibonacciRetracement(swing_start, swing_end)

        swing_df = df.loc[swing_start.datetime:swing_end.datetime]
        pullback_df = df.loc[swing_end.datetime:retracement.datetime]

        is_bullish_swing = swing_end.price > swing_start.price

        is_valid_swing = is_n_non_indecision_candles(swing_df, 2) and is_n_candles(swing_df, 2, is_bullish_swing)
        is_valid_pullback = is_n_non_indecision_candles(pullback_df, 2) and is_n_candles(pullback_df, 2, not is_bullish_swing)

        is_valid_fibonacci_retracement = fibonacci_retracement.is_healthy_retracement(retracement.price)

        return is_valid_swing and (is_valid_pullback or is_valid_fibonacci_retracement)
