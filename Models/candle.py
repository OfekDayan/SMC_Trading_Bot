from datetime import timedelta
import plotly.graph_objects as go

from constants import TIME_FRAME
from tools.horizontal_trend_line import HorizontalTrendLine


class Candle:
    def __init__(self, time, row):
        self.time = time
        self.open_price = row['Open']
        self.close_price = row['Close']
        self.high_price = row['High']
        self.low_price = row['Low']
        self.__row = row

    def is_bullish(self) -> bool:
        return self.close_price > self.open_price

    def is_bearish(self) -> bool:
        return self.open_price > self.close_price

    def body_size(self) -> float:
        return abs(self.open_price - self.close_price)

    def is_imbalance(self) -> bool:
        if self.__row['Imbalance'] == 0:
            return False

        body_size = self.body_size()
        imbalance_body_ratio = self.__row['Imbalance'] / body_size

        # return imbalance_body_ratio >= 0.3
        return True

    def plot_imbalance(self, figure: go.Figure):
        if not self.is_imbalance():
            return

        single_candle_timedelta = self.__parse_timedelta(TIME_FRAME)
        from_time = self.time - single_candle_timedelta
        to_time = self.time + single_candle_timedelta
        imbalance_start = self.__row['Imbalance_Start']
        imbalance_end = self.__row['Imbalance_End']

        bottom_line = HorizontalTrendLine('', from_time, to_time, imbalance_start)
        top_line = HorizontalTrendLine('', from_time, to_time, imbalance_end)

        bottom_line.plot(figure, 'black')
        top_line.plot(figure, 'black')

    def plot_type(self, figure: go.Figure):
        figure.add_trace(
            go.Scatter(
                x=[self.time],
                y=[self.close_price],
                mode='text',
                text=self.get_candle_type(),
                textposition="top center",
                textfont=dict(color="black")
            )
        )

    def is_big_candle(self):
        return self.__row['is_big_candle']

    def is_indecision(self):
        return self.is_doji() or self.is_doji_star() or self.is_dragonfly_doji() or self.is_gravestone_doji() or self.is_long_legged__doji() or \
               self.is_hammer() or self.is_inverted_hammer() or self.is_spinning_top() or self.is_hanging_man() or self.is_shooting_star()

    def is_reversal(self):
        if self.is_bullish():
            return (
                self.is_hammer() or
                self.is_inverted_hammer() or
                self.is_piercing_line() or
                self.is_bullish_engulfing() or
                self.is_morning_star()
            )
        else:
            return (
                self.is_shooting_star() or
                self.is_hanging_man() or
                self.is_dark_cloud_cover() or
                self.is_bearish_engulfing() or
                self.is_evening_star()
            )

    # Bullish Reversal Patterns
    def is_hammer(self):
        return self.__row['CDLHAMMER']

    def is_inverted_hammer(self):
        return self.__row['CDLINVERTEDHAMMER']

    def is_piercing_line(self):
        return self.__row['CDLPIERCING']

    def is_bullish_engulfing(self):
        return self.is_bullish() and self.is_engulfing()

    def is_morning_star(self):
        return self.__row['CDLMORNINGSTAR']

    # Bearish Reversal Patterns
    def is_shooting_star(self):
        return self.__row['CDLSHOOTINGSTAR']

    def is_hanging_man(self):
        return self.__row['CDLHANGINGMAN']

    def is_dark_cloud_cover(self):
        return self.__row['CDLDARKCLOUDCOVER']

    def is_bearish_engulfing(self):
        return not self.is_bullish() and self.is_engulfing()

    def is_evening_star(self):
        return self.__row['CDLEVENINGSTAR']

    def is_doji(self):
        return self.__row['CDLDOJI']

    def is_doji_star(self):
        return self.__row['CDLDOJISTAR']

    def is_dragonfly_doji(self):
        return self.__row['CDLDRAGONFLYDOJI']

    def is_gravestone_doji(self):
        return self.__row['CDLGRAVESTONEDOJI']

    def is_long_legged__doji(self):
        return self.__row['CDLLONGLEGGEDDOJI']

    def is_spinning_top(self):
        return False
        # return self.__row['CDLSPINNINGTOP']

    # Momentum
    def is_marubozu(self):
        return self.__row['CDLMARUBOZU']

    def is_engulfing(self):
        return self.__row['CDLENGULFING']

    def get_candle_type(self) -> str:
        if self.is_hammer():
            return "Hammer"
        elif self.is_inverted_hammer():
            return "Inverted Hammer"
        elif self.is_piercing_line():
            return "Piercing Line"
        elif self.is_engulfing():
            return "Engulfing"
        elif self.is_morning_star():
            return "Morning Star"
        elif self.is_marubozu():
            return "Marubozu"
        elif self.is_spinning_top():
            return "Spinning Top"
        elif self.is_long_legged__doji():
            return "Doji"
        elif self.is_gravestone_doji():
            return "Gravestone Doji"
        elif self.is_shooting_star():
            return "Shooting Star"
        elif self.is_hanging_man():
            return "Hanging Man"
        elif self.is_dark_cloud_cover():
            return "Dark Cloud Cover"
        elif self.is_evening_star():
            return "Evening Star"
        else:
            return ""

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
