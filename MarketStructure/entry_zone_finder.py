import pandas
from typing import List
from MarketStructure.pivot_points import PivotPoints
from Models.candle import Candle
from tools.order_block import OrderBlock
from tools.point import Point
import plotly.graph_objects as go
from tools.horizontal_trend_line import HorizontalTrendLine


def find(choches_and_boses: List[HorizontalTrendLine], market_structure_points: List[Point], figure: go.Figure, df: pandas.DataFrame):
    for smc_level in choches_and_boses:
        # find the pivot point caused the BOS / CHoCH
        before_pivot_point = [date for date in market_structure_points if date.datetime < smc_level.to_datetime][-1]

        # slice entry zone dataframe
        entry_zone_df = df.loc[before_pivot_point.datetime:smc_level.to_datetime]

        # find pivot points in minor entry zone trend
        pivot_points = PivotPoints(entry_zone_df)
        pivot_points.find()
        pivot_points.plot_pivot_points(figure)

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

        while (is_bullish and institutional_candle.is_bullish()) or (not is_bullish and institutional_candle.is_bearish()):
            # take one candle before
            current_candle_index = df.index.get_loc(institutional_candle.time)
            previous_candle_row = df.iloc[current_candle_index - 1]
            institutional_candle = Candle(previous_candle_row.name, previous_candle_row)

        # initiate ODB
        odb_bottom_left = Point(institutional_candle.time, institutional_candle.low_price)
        odb_top_right = Point(df.index[-1], institutional_candle.high_price)
        order_block = OrderBlock(odb_bottom_left, odb_top_right, is_bullish)

        # find the pivot point after BOS / CHoCH
        next_pivot_point_index = market_structure_points.index(before_pivot_point) + 1

        if next_pivot_point_index < len(market_structure_points):  # next pivot point exists?
            after_pivot_point = market_structure_points[next_pivot_point_index]
            order_block_pullback_df = df.loc[after_pivot_point.datetime:]

            # check if order block is touched
            for candle_time, row in order_block_pullback_df.iterrows():
                candle = Candle(candle_time, row)

                if order_block.is_touched_rectangle(candle.low_price) or order_block.is_touched_rectangle(candle.high_price):
                    order_block.set_as_touched(candle_time)
                    break

            # plot order block
            order_block.plot(df, figure)

