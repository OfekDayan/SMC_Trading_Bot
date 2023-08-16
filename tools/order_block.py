from datetime import datetime
import pandas
import plotly.graph_objects as go
from tools.point import Point
from user_options import UserOption


class OrderBlock:
    def __init__(self, bottom_left: Point, top_right: Point, symbol: str, is_bullish: bool):
        self.bottom_left = bottom_left
        self.top_right = top_right
        self.is_bullish = is_bullish
        self.is_touched = False
        self.is_failed = False
        self.user_decision = UserOption.NONE
        self.ninty_percent_fibo_price = None
        self.symbol = symbol
        self.id = int(self.bottom_left.datetime.timestamp())

    def get_top_left(self):
        return Point(self.bottom_left.datetime, self.top_right.price)

    def set_as_touched(self, touching_datetime: datetime):
        self.is_touched = True
        self.top_right.datetime = touching_datetime

    def set_as_failed(self, touching_datetime: datetime):
        self.is_failed = True
        self.top_right.datetime = touching_datetime

    def plot(self, df: pandas.DataFrame, figure: go.Figure):
        timeframe = self.__get_timeframe(df)

        if self.is_touched:
            color = "Blue"
            name = f'{timeframe} Mitigation'

        elif self.is_failed:
            color = "Black"
            name = f'{timeframe} Failed'
        else:
            color = "Green" if self.is_bullish else "Red"
            name = f'{timeframe} ODB'

        x0 = self.bottom_left.datetime
        y0 = self.bottom_left.price
        x1 = self.top_right.datetime
        y1 = self.top_right.price

        # plot rectangle
        figure.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=color, opacity=0.3, line=dict(color=color))

        # plot name
        y = y0 + (y1 - y0) / 2.0
        figure.add_trace(go.Scatter(x=[x0, x0 + (x1 - x0) / 2.0, x1], y=[y, y, y], mode='lines+text', name=name,
                                    line=dict(color=color, width=0), text=['', name, ''],
                                    textposition="middle center"))


    def is_touched_rectangle(self, price: float) -> bool:
        return self.bottom_left.price <= price <= self.top_right.price

    def __get_timeframe(self, df: pandas.DataFrame) -> str:
        timeframe = df.index[1] - df.index[0]

        if timeframe.components.days > 0:
            return f'{timeframe.components.days}D'

        elif timeframe.components.hours > 0:
            return f'{timeframe.components.hours}H'

        elif timeframe.components.minutes > 0:
            return f'{timeframe.components.minutes}m'

        return None