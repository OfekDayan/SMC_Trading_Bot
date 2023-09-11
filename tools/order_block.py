from datetime import datetime
from enum import Enum

import pandas
import plotly.graph_objects as go

from Models.candle import Candle
from Models.position import Position, LongPosition, ShortPosition
from tools.point import Point
from user_options import UserOption


class OrderBlockStatus(Enum):
    UNKNOWN = 0
    OUT_OF_RANGE = 1
    HIT_SL = 2
    HIT_TL = 3
    TRADING = 4
    TRADED = 5


class OrderBlock:
    def __init__(self, bottom_left: Point, top_right: Point, symbol: str, is_bullish: bool):
        self.bottom_left = bottom_left
        self.top_right = top_right
        self.is_bullish = is_bullish
        self.order_block_status = OrderBlockStatus.UNKNOWN
        self.user_decision = UserOption.NONE
        self.ninty_percent_fibo_price = None
        self.symbol = symbol
        self.id = int(self.bottom_left.datetime.timestamp())
        self.is_tl_sl_message_sent = False

    def get_top_left(self):
        return Point(self.bottom_left.datetime, self.top_right.price)

    def set_end_time(self, end_time: datetime):
        self.top_right.datetime = end_time

    def get_end_time(self):
        return self.top_right.datetime

    def plot(self, df: pandas.DataFrame, figure: go.Figure):
        # timeframe = self.__get_timeframe(df)
        name = f'Order Block'
        color = 'White'

        match self.order_block_status:
            case OrderBlockStatus.UNKNOWN:
                color = "White"

            case OrderBlockStatus.OUT_OF_RANGE:
                color = "Black"

        if self.user_decision == UserOption.TRADE:
            match self.order_block_status:
                case OrderBlockStatus.HIT_SL:
                    color = "Red"

                case OrderBlockStatus.HIT_TL:
                    color = "Green"

                case OrderBlockStatus.TRADING:
                    color = "Blue"

        x0 = self.bottom_left.datetime
        y0 = self.bottom_left.price
        x1 = self.top_right.datetime
        y1 = self.top_right.price

        # plot rectangle
        figure.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=color, opacity=0.4, line=dict(color=color))

        # plot name
        y = y0 + (y1 - y0) / 2.0
        figure.add_trace(go.Scatter(x=[x0, x0 + (x1 - x0) / 2.0, x1], y=[y, y, y], mode='lines+text', name=name,
                                    line=dict(color=color, width=0), text=['', name, ''],
                                    textposition="middle center"))

    def get_position(self):
        SL_TP_RATIO = 1.5

        # half_order_block_size = (self.top_right.price - self.bottom_left.price) / 2
        half_order_block_size = (self.top_right.price - self.bottom_left.price) * 1.5

        if self.is_bullish:
            sl_price = self.bottom_left.price - half_order_block_size
            entry_price = self.top_right.price
            tl_price = entry_price + ((entry_price - sl_price) * SL_TP_RATIO)

            return LongPosition(entry_price, sl_price, tl_price)

        else:
            sl_price = self.top_right.price + half_order_block_size
            entry_price = self.bottom_left.price
            tl_price = entry_price - ((sl_price - entry_price) * SL_TP_RATIO)

            return ShortPosition(entry_price, sl_price, tl_price)

    def is_candle_touch(self, candle: Candle):
        return self.is_touched_rectangle(candle.low_price) or self.is_touched_rectangle(candle.high_price)

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