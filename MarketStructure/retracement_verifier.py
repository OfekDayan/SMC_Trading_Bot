from datetime import timedelta
import pandas
from MarketStructure.candles_counter import is_n_non_indecision_candles, is_n_candles, is_n_non_reversal_candles
from tools.fibonacci_retracement import FibonacciRetracement
from tools.point import Point


class RetracementVerifier:

    def is_valid(self, df: pandas.DataFrame, swing_start: Point, swing_end: Point, retracement: Point, timeframe):
        if df.empty:
            return False

        fibonacci_retracement = FibonacciRetracement(swing_start, swing_end)

        single_candle_timedelta = self.__parse_timedelta(timeframe)

        swing_df = df.loc[swing_start.datetime + single_candle_timedelta:swing_end.datetime + single_candle_timedelta]
        pullback_df = df.loc[swing_end.datetime + single_candle_timedelta:retracement.datetime + single_candle_timedelta]

        is_bullish_swing = swing_end.price > swing_start.price

        is_valid_swing = is_n_non_indecision_candles(swing_df, 1, timeframe) and \
                         is_n_non_reversal_candles(swing_df, 1, timeframe) and \
                         is_n_candles(swing_df, 3, timeframe, is_bullish_swing)

        is_valid_pullback = is_n_non_indecision_candles(pullback_df, 1, timeframe) and \
                            is_n_non_reversal_candles(pullback_df, 1, timeframe) and \
                            is_n_candles(pullback_df, 3, timeframe, not is_bullish_swing)

        is_valid_fibonacci_retracement = fibonacci_retracement.is_healthy_retracement(retracement.price)

        return is_valid_swing and (is_valid_pullback or (is_valid_fibonacci_retracement and is_n_candles(pullback_df, 3, timeframe, not is_bullish_swing)))

    def __parse_timedelta(self, duration_str):
        unit_mapping = {
            's': 'seconds',
            'm': 'minutes',
            'h': 'hours',
            'd': 'days',
            'w': 'weeks'
        }

        duration = int(duration_str[:-1])
        unit = unit_mapping.get(duration_str[-1])

        if unit:
            return timedelta(**{unit: duration})
        else:
            raise ValueError("Invalid duration format")