from datetime import datetime
import plotly.graph_objects as go


class Point:
    def __init__(self, date_time: datetime, price, name: str = ''):
        self.datetime = date_time
        self.price = price
        self.name = name

    def plot(self, figure: go.Figure, color: str, marker_size: int = 7):
        scatter = go.Scatter(
                x=[self.datetime],
                y=[self.price],
                mode='markers+text',
                text=self.name,
                textposition="top center",
                line=dict(color=color),
                marker=dict(size=marker_size),
                textfont=dict(color=color)
            )

        figure.add_trace(scatter)
        return scatter
