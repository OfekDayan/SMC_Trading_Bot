from datetime import datetime
import plotly.graph_objects as go
from tools.point import Point


class HorizontalTrendLine:
    def __init__(self, name: str, from_datetime: datetime, to_datetime: datetime, price):
        self.from_datetime = from_datetime
        self.to_datetime = to_datetime
        self.price = price
        self.name = name

    def time_diff(self):
        return self.to_datetime - self.from_datetime

    def plot(self, figure: go.Figure, color: str):
        x1 = self.from_datetime
        x2 = self.to_datetime
        y = self.price

        figure.add_trace(go.Scatter(x=[x1, x2], y=[y, y], mode='lines', name=self.name, line=dict(color=color)))

        if self.name:
            x = x1 + (x2 - x1) / 2.0
            label_point = Point(x, y, self.name)
            label_point.plot(figure, color)
