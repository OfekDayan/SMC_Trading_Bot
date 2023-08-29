from datetime import datetime
from abc import ABC, abstractmethod
import plotly.graph_objects as go

from tools.point import Point


class Position(ABC):
    def __init__(self, entry: float, stop_loss: float, take_profit: float):
        self.entry = entry
        self.stop_loss = stop_loss
        self.take_profit = take_profit

    def plot_rectangle(self, bottom_left: Point, top_right: Point, figure: go.Figure, color: str):
        figure.add_shape(type="rect",
                         x0=bottom_left.datetime,
                         y0=bottom_left.price,
                         x1=top_right.datetime,
                         y1=top_right.price,
                         fillcolor=color, opacity=0.3, line=dict(color=color))

    @abstractmethod
    def plot(self, start: datetime, end: datetime, figure: go.Figure):
        pass


class LongPosition(Position):
    def plot(self, start: datetime, end: datetime, figure: go.Figure):
        # Stop loss area
        bottom_left = Point(start, self.stop_loss)
        top_right = Point(end, self.entry)
        super().plot_rectangle(bottom_left, top_right, figure, "Red")

        # Take profit area
        bottom_left = Point(start, self.entry)
        top_right = Point(end, self.take_profit)
        super().plot_rectangle(bottom_left, top_right, figure, "Green")


class ShortPosition(Position):
    def plot(self, start: datetime, end: datetime, figure: go.Figure):
        # Stop loss area
        bottom_left = Point(start, self.entry)
        top_right = Point(end, self.stop_loss)
        super().plot_rectangle(bottom_left, top_right, figure, "Red")

        # Take profit area
        bottom_left = Point(start, self.take_profit)
        top_right = Point(end, self.entry)
        super().plot_rectangle(bottom_left, top_right, figure, "Green")
