from datetime import datetime
import plotly.graph_objects as go


class Point:
    def __init__(self, datetime: datetime, price, name: str = ''):
        self.datetime = datetime
        self.price = price
        self.name = name

    def plot(self, figure: go.Figure, color: str):
        figure.add_trace(
            go.Scatter(
                x=[self.datetime],
                y=[self.price],
                mode='markers+text',
                text=self.name,
                textposition="top center",
                line=dict(color=color)
            )
        )
