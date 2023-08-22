from datetime import datetime
import plotly.graph_objects as go


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

        scatter = go.Scatter(x=[x1, x1 + (x2 - x1) / 2.0, x2], y=[y, y, y], mode='lines+text', name=self.name,
                             line=dict(color=color), text=['', self.name, ''], textposition="top center")

        figure.add_trace(scatter)
        return scatter
