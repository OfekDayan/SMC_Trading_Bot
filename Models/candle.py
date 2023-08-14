from datetime import timedelta
import plotly.graph_objects as go
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

        from_time = self.time
        to_time = self.time + timedelta(hours=2)
        imbalance_start = self.__row['Imbalance_Start']
        imbalance_end = self.__row['Imbalance_End']

        bottom_line = HorizontalTrendLine('', from_time, to_time, imbalance_start)
        top_line = HorizontalTrendLine('', from_time, to_time, imbalance_end)

        bottom_line.plot(figure, 'black')
        top_line.plot(figure, 'black')

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
        return self.__row['Hammer']

    def is_inverted_hammer(self):
        return self.__row['Inverted_hammer']

    def is_piercing_line(self):
        return self.__row['Piercing_line']

    def is_bullish_engulfing(self):
        return self.is_bullish() and self.__row['Engulfing']

    def is_morning_star(self):
        return self.__row['Morning_tar']

    # Bearish Reversal Patterns
    def is_shooting_star(self):
        return self.__row['Shooting_star']

    def is_hanging_man(self):
        return self.__row['Hanging_man']

    def is_dark_cloud_cover(self):
        return self.__row['Dark_cloud_cover']

    def is_bearish_engulfing(self):
        return not self.is_bullish() and self.__row['Engulfing']

    def is_evening_star(self):
        return self.__row['Evening_star']

    def is_indecision(self):
        return self.is_doji() or self.is_doji_star() or self.is_dragonfly_doji() or self.is_gravestone_doji() or self.is_long_legged__doji() or \
               self.is_hammer() or self.is_inverted_hammer() or self.is_spinning_top() or self.is_hanging_man() or self.is_shooting_star()

    def is_doji(self):
        return self.__row['Doji']

    def is_doji_star(self):
        return self.__row['Doji_star']

    def is_dragonfly_doji(self):
        return self.__row['Dragonfly_doji']

    def is_gravestone_doji(self):
        return self.__row['Gravestone_doji']

    def is_long_legged__doji(self):
        return self.__row['Long_legged_doji']

    def is_spinning_top(self):
        return self.__row['Spinning_top']

    # Momentum
    def is_marubozu(self):
        return self.__row['Marubozu']

    def is_engulfing(self):
        return self.__row['Engulfing']

    def get_candle_type(self) -> str:
        if self.is_reversal():
            if self.is_bullish():
                if self.is_hammer():
                    return "Bullish Hammer"
                elif self.is_inverted_hammer():
                    return "Bullish Inverted Hammer"
                elif self.is_piercing_line():
                    return "Bullish Piercing Line"
                elif self.is_bullish_engulfing():
                    return "Bullish Engulfing"
                elif self.is_morning_star():
                    return "Bullish Morning Star"
            else:
                if self.is_shooting_star():
                    return "Bearish Shooting Star"
                elif self.is_hanging_man():
                    return "Bearish Hanging Man"
                elif self.is_dark_cloud_cover():
                    return "Bearish Dark Cloud Cover"
                elif self.is_bearish_engulfing():
                    return "Bearish Engulfing"
                elif self.is_evening_star():
                    return "Bearish Evening Star"
        elif self.is_indecision():
            return "Indecision Candle"
        elif self.is_marubozu():
            return "Marubozu Candle"
        else:
            return "Normal Candle"
