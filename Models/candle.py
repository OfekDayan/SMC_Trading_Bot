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

        return imbalance_body_ratio >= 0.5 and not self.is_indecision()

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

    # Indecision
    def is_indecision(self):
        return self.is_doji() or self.is_doji_star() or self.is_dragonfly_doji() or self.is_gravestone_doji() or self.is_long_legged__doji() or \
               self.is_pinbar() or self.is_inverted_pinbar() or self.is_spinning_top() or self.is_hanging_man() or self.is_shooting_star()

    def is_doji(self):
        return self.__row['Doji']

    def is_doji_star(self):
        return self.__row['Doji_Star']

    def is_dragonfly_doji(self):
        return self.__row['Dragonfly_Doji']

    def is_gravestone_doji(self):
        return self.__row['Gravestone_Doji']

    def is_long_legged__doji(self):
        return self.__row['Long_Legged_Doji']

    def is_pinbar(self):
        return self.__row['Pinbar']

    def is_inverted_pinbar(self):
        return self.__row['Inverted_Pinbar']

    def is_spinning_top(self):
        return self.__row['Spinning_Top']

    def is_hanging_man(self):
        return self.__row['Hanging_Man']

    def is_shooting_star(self):
        return self.__row['Shooting_Star']

    # Momentum
    def is_marubozu(self):
        return self.__row['Marubozu']

    def is_engulfing(self):
        return self.__row['Engulfing']

    def get_type(self):
        if self.is_doji():
            return 'doji'

        if self.is_doji_star():
            return 'doji star'

        if self.is_dragonfly_doji():
            return 'dragonfly doji'

        if self.is_gravestone_doji():
            return 'gravestone doji'

        if self.is_long_legged__doji():
            return 'long legged doji'

        if self.is_pinbar():
            return 'pinbar'

        if self.is_inverted_pinbar():
            return 'inverted pinbar'

        if self.is_spinning_top():
            return 'spinning top'

        if self.is_hanging_man():
            return 'hanging man'

        if self.is_shooting_star():
            return 'shooting star'

        if self.is_marubozu():
            return 'marubozu'

        # if self.is_engulfing():
        #     return 'engulfing'

        else:
            return None