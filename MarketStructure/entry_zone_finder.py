from datetime import timedelta
import pandas
from typing import List
from MarketStructure.pivot_points import PivotPoints
from Models.candle import Candle
from tools.order_block import OrderBlock
from tools.point import Point
import plotly.graph_objects as go
from tools.horizontal_trend_line import HorizontalTrendLine


def find(choches_and_boses: List[HorizontalTrendLine], market_structure_points: List[Point], figure: go.Figure,
         df: pandas.DataFrame):
    for smc_level in choches_and_boses:
        before_pivot_point = [date for date in market_structure_points if date.datetime < smc_level.to_datetime][-1]

        entry_zone_df = df.loc[before_pivot_point.datetime:smc_level.to_datetime]

        # find pivot points in minor entry zone trend
        pivot_points = PivotPoints(entry_zone_df)
        pivot_points.find()
        pivot_points.add_to_chart(figure)

        # find last pivot point caused the CHOCH/BOS
        if pivot_points.market_structure_points:
            pivot_point_starts_the_swing = pivot_points.market_structure_points[-1]
        else:  # no minor trend
            pivot_point_starts_the_swing = before_pivot_point

        is_bullish = smc_level.price > before_pivot_point.price

        if is_bullish:

            if pivot_point_starts_the_swing.name == 'HL' or pivot_point_starts_the_swing.name == 'LL':  # last bottom found!
                pass
            else:
                print("need to find entry in lower TF!")
                continue
        else:   # bearish
            if pivot_point_starts_the_swing.name == 'LH' or pivot_point_starts_the_swing.name == 'HH':  # last top found!
                pass
            else:
                print("need to find entry in lower TF!")
                continue

        # find the institutional candle
        institutional_candle = Candle(pivot_point_starts_the_swing.datetime, df.loc[pivot_point_starts_the_swing.datetime])

        if (is_bullish and institutional_candle.is_bullish()) or (not is_bullish and institutional_candle.is_bearish()):
            # take one candle before
            institutional_candle = Candle(pivot_point_starts_the_swing.datetime, df.loc[pivot_point_starts_the_swing.datetime].shift(1))

        # plot ODB
        odb_bottom_left = Point(institutional_candle.time, institutional_candle.low_price)
        odb_top_right = Point(institutional_candle.time + timedelta(hours=5), institutional_candle.high_price)

        order_block = OrderBlock(odb_bottom_left, odb_top_right, '15m')
        order_block.plot(figure)

        # x0 = institutional_candle.time
        # y0 = institutional_candle.low_price
        # x1 = institutional_candle.time + timedelta(hours=5)
        # y1 = institutional_candle.high_price
        #
        # figure.add_shape(type="rect",
        #                  x0=x0,
        #                  y0=y0,
        #                  x1=x1,
        #                  y1=y1,
        #                  line=dict(color="RoyalBlue"),
        #                  )
