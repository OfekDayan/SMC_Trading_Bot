from datetime import datetime
import plotly.graph_objects as go
from tools.point import Point

level_and_color = {
    0: 'green',
    38.2: 'red',
    50: 'orange',
    61.8: 'yellow',
    80: 'yellow',
    100: 'blue'
}


class FibonacciRetracement:
    def __init__(self, swing_start: Point, swing_end: Point):
        self.swing_start = swing_start
        self.swing_end = swing_end

    def plot(self, figure: go.Figure, to_time: datetime):
        from_time = self.swing_start.datetime

        for level, color in level_and_color.items():
            price = self.__get_level_price(level)
            figure.add_trace(go.Scatter(x=[from_time, to_time], y=[price, price], mode='lines', name=f'Fibo {level}%',
                                        line=dict(color=color, dash='dash')))

            figure.add_trace(go.Scatter(x=[to_time], y=[price], mode='markers+text', text=f'{level}%', line=dict(color=color), textposition="top right"))

        figure.update_layout(xaxis_rangeslider_visible=False)
        figure.show()

    def is_healthy_retracement(self, retracement_price: float):
        retracement_level = 38.2
        return retracement_price <= self.__get_level_price(retracement_level)

    def __get_level_price(self, level: float) -> float:
        from_price = self.swing_start.price
        to_price = self.swing_end.price
        range = abs(from_price - to_price)
        level_range = range * (level / 100.0)
        return to_price - level_range if from_price < to_price else to_price + level_range

