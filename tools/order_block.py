from datetime import datetime
import plotly.graph_objects as go
from tools.point import Point


class OrderBlock:
    def __init__(self, bottom_left: Point, top_right: Point, timeframe: str = ''):
        self.bottom_left = bottom_left
        self.top_right = top_right
        self.timeframe = timeframe

    def plot(self, figure: go.Figure):
        x0 = self.bottom_left.datetime
        y0 = self.bottom_left.price
        x1 = self.top_right.datetime
        y1 = self.top_right.price

        # plot rectangle
        figure.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor="LightGreen", opacity=0.5, line=dict(color="LightGreen"))

        # plot name
        if self.timeframe:
            x = x0 + (x1 - x0) / 2.0
            y = y0 + (y1 - y0) / 2.0
            label_point = Point(x, y, f'{self.timeframe}ODB')
            label_point.plot(figure, 'black')
