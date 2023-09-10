import pandas
from typing import List
from MarketStructure.pivot_points_detector import PivotPointsDetector
from Models.candle import Candle
from Models.entry_zone import EntryZone
from tools.order_block import OrderBlock, OrderBlockStatus
from tools.point import Point
import plotly.graph_objects as go
from tools.horizontal_trend_line import HorizontalTrendLine


class EntryZoneFinder:
    def __init__(self, df: pandas.DataFrame, figure: go.Figure, symbol: str, timeframe):
        self.figure = figure
        self.df = df
        self.symbol = symbol
        self.timeframe = timeframe

    def find(self, choches_and_boses: List[HorizontalTrendLine], market_structure_points: List[Point]) -> list[(OrderBlock, pandas.DataFrame)]:
        order_blocks_and_pullback_df = []

        for smc_level in choches_and_boses:
            # find the pivot point caused the BOS / CHoCH
            before_pivot_point = [date for date in market_structure_points if date.datetime < smc_level.to_datetime][-1]

            # slice entry zone dataframe
            entry_zone_df = self.df.loc[before_pivot_point.datetime:smc_level.to_datetime]
            is_bullish = smc_level.price > before_pivot_point.price

            entry_zone = EntryZone(entry_zone_df, is_bullish)
            pivot_point_starts_the_swing = self.__find_pivot_point_caused_bos_choch(before_pivot_point, entry_zone)

            if pivot_point_starts_the_swing is None:
                continue

            institutional_candle = self.__find_institutional_candle(pivot_point_starts_the_swing, is_bullish)

            order_block = self.__get_order_block(institutional_candle, is_bullish)

            # find the pivot point after BOS / CHoCH
            after_pivot_point_index = market_structure_points.index(before_pivot_point) + 1

            if after_pivot_point_index < len(market_structure_points):  # next pivot point exists?
                after_pivot_point = market_structure_points[after_pivot_point_index]

                # Check if BOS/CHoCH is not crossing between the same pivot points type - ex: HH -> CHoCH -> CHoCH -> HH
                if after_pivot_point.name == before_pivot_point.name:
                    continue

                # Check if there is at least 1 imbalance caused by the order block
                active_zone_df = self.df.loc[pivot_point_starts_the_swing.datetime:after_pivot_point.datetime]
                imbalances_counter = 0
                big_candle_counter = 0

                is_valid_active_zone = False

                for index, row in active_zone_df.iterrows():
                    candle = Candle(index, row, self.timeframe)

                    if candle.is_imbalance():
                        imbalances_counter += 1

                    if candle.is_big_candle():
                        big_candle_counter += 1

                    # 1 candle with imbalances were found & at least 1 big candle
                    if imbalances_counter >= 1 and big_candle_counter >= 1:
                        is_valid_active_zone = True
                        break

                if not is_valid_active_zone:
                    continue

                self.__check_order_block_status(order_block, after_pivot_point)
                order_block_pullback_df = self.df.loc[after_pivot_point.datetime:order_block.get_end_time()]

                order_blocks_and_pullback_df.append((order_block, order_block_pullback_df))

        return order_blocks_and_pullback_df

    def __check_order_block_status(self, order_block: OrderBlock, after_pivot_point: Point):
        touching_candle = None
        after_pullback_df = self.df.loc[after_pivot_point.datetime:]

        is_touch = False

        # Check touching point
        for candle_time, row in after_pullback_df.iterrows():
            candle = Candle(candle_time, row, self.timeframe)

            if order_block.is_candle_touch(candle):
                is_touch = True
                touching_candle = candle
                break

            if (order_block.is_bullish and candle.close_price > after_pivot_point.price) or (not order_block.is_bullish and candle.close_price < after_pivot_point.price):
                order_block.order_block_status = OrderBlockStatus.OUT_OF_RANGE
                order_block.set_end_time(candle.time)
                return

        if not is_touch:
            return

        order_block.order_block_status = OrderBlockStatus.TRADING

        # order block is touched!
        after_touching_df = after_pullback_df.loc[touching_candle.time:]

        # get position
        position = order_block.get_position()
        end_position_time = None

        # Check position levels
        for candle_time, row in after_touching_df.iterrows():
            candle = Candle(candle_time, row, self.timeframe)

            if not order_block.is_bullish:
                if candle.high_price > position.stop_loss:
                    order_block.order_block_status = OrderBlockStatus.HIT_SL
                    end_position_time = candle.time
                    order_block.set_end_time(end_position_time)
                    break

                if candle.low_price <= position.take_profit:
                    order_block.order_block_status = OrderBlockStatus.HIT_TL
                    end_position_time = candle.time
                    order_block.set_end_time(end_position_time)
                    break

            if order_block.is_bullish:
                if candle.low_price < position.stop_loss:
                    order_block.order_block_status = OrderBlockStatus.HIT_SL
                    end_position_time = candle.time
                    order_block.set_end_time(end_position_time)
                    break

                if candle.high_price >= position.take_profit:
                    order_block.order_block_status = OrderBlockStatus.HIT_TL
                    end_position_time = candle.time
                    order_block.set_end_time(end_position_time)
                    break

        until_time = end_position_time

        if until_time is None:
            until_time = after_touching_df.index[-1]

        start_position_time = touching_candle.time
        position.plot(start_position_time, until_time, self.figure)


    def __get_order_block(self, institutional_candle: Candle, is_bullish: bool) -> OrderBlock:
        odb_bottom_left = Point(institutional_candle.time, institutional_candle.low_price)
        odb_top_right = Point(self.df.index[-1], institutional_candle.high_price)
        return OrderBlock(odb_bottom_left, odb_top_right, self.symbol, is_bullish)

    def __find_institutional_candle(self, pivot_point_starts_the_swing: Point, is_bullish: bool) -> Candle:
        # find the institutional candle
        institutional_candle = Candle(pivot_point_starts_the_swing.datetime,
                                      self.df.loc[pivot_point_starts_the_swing.datetime], self.timeframe)

        while (is_bullish and institutional_candle.is_bullish()) or (
                not is_bullish and institutional_candle.is_bearish()):
            # take one candle before
            current_candle_index = self.df.index.get_loc(institutional_candle.time)
            previous_candle_row = self.df.iloc[current_candle_index - 1]
            institutional_candle = Candle(previous_candle_row.name, previous_candle_row, self.timeframe)

        return institutional_candle

    def __find_pivot_point_caused_bos_choch(self, suspected_pivot_point: Point, entry_zone: EntryZone) -> Point:
        # find minor's trend pivot points
        pivot_points_detector = PivotPointsDetector(entry_zone.df, self.timeframe)
        pivot_points_detector.find()
        pivot_points_detector.plot_pivot_points(self.figure, 3, 'gray')

        # find last pivot point caused the CHOCH/BOS
        if pivot_points_detector.pivot_points:
            pivot_point_starts_the_swing = pivot_points_detector.pivot_points[-1]

        else:  # no minor trend
            pivot_point_starts_the_swing = suspected_pivot_point

        # if entry_zone.is_bullish:
        #
        #     if pivot_point_starts_the_swing.name == 'HL' or pivot_point_starts_the_swing.name == 'LL':  # last bottom found!
        #         pass
        #
        #     else:
        #         print("need to find entry in lower TF!")
        #         pivot_point_starts_the_swing = None
        #
        # else:  # bearish
        #
        #     if pivot_point_starts_the_swing.name == 'LH' or pivot_point_starts_the_swing.name == 'HH':  # last top found!
        #         pass
        #
        #     else:
        #         print("need to find entry in lower TF!")
        #         pivot_point_starts_the_swing = None

        return pivot_point_starts_the_swing
