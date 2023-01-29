import pandas
from Models.candle import Candle


def is_n_non_indecision_candles(df: pandas.DataFrame, n: int, is_bullish: bool = True):
    valid_candles = 0

    for index, row in df.iterrows():
        candle = Candle(index, row)

        if (is_bullish and candle.is_bullish()) or (not is_bullish and candle.is_bearish()) and not candle.is_indecision():
            valid_candles += 1

            if valid_candles == n:
                return True

    return False


def is_n_consecutive_non_indecision_candles(df: pandas.DataFrame, n: int, is_bullish: bool = True):
    valid_candles = 0

    for index, row in df.iterrows():
        candle = Candle(index, row)

        if (is_bullish and candle.is_bullish()) or (not is_bullish and candle.is_bearish()):
            if candle.is_indecision():
                valid_candles = 0
            else:
                valid_candles += 1

                if valid_candles == n:
                    return True


    return False


def is_n_candles(df: pandas.DataFrame, n: int, is_bullish: bool = True):
    valid_candles = 0

    for index, row in df.iterrows():
        candle = Candle(index, row)

        if (is_bullish and candle.is_bullish()) or (not is_bullish and candle.is_bearish()):
            valid_candles += 1

            if valid_candles == n:
                return True

    return False


