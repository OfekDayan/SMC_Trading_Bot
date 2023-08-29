import shutil
from datetime import datetime

import pandas as pd
from Models.candle import Candle
import plotly.graph_objects as go
from MarketStructure.retracement_verifier import RetracementVerifier
from tools.fibonacci_retracement import FibonacciRetracement
from tools.horizontal_trend_line import HorizontalTrendLine
from tools.point import Point
import os
import cv2

IMAGES_FOLDER = "pivot_points_animation"


class PivotPointsDetector:
    def __init__(self, df: pd.DataFrame, is_animation_mode: bool = False):
        self.df = df
        self.temp_df = df.copy()  # Create a copy of the original DataFrame
        self.__trend = None
        self.current_candle_index = 0
        self.retracement_verifier = RetracementVerifier()
        self.low = None
        self.high = None
        self.dynamic_low = None
        self.dynamic_high = None
        self.choches_and_boses = []
        self.pivot_points = []
        self.animation_chart = None
        self.animation_index = 0

        if is_animation_mode:
            self.delete_and_create_folder(IMAGES_FOLDER)
            self.animation_chart = go.Figure(data=[go.Candlestick(x=self.df.index, open=self.df['Open'], high=self.df['High'], low=self.df['Low'], close=self.df['Close'])])

    def __find_trend(self):
        max_high_value = self.temp_df['High'].idxmax()
        min_low_value = self.temp_df['Low'].idxmin()

        if max_high_value < min_low_value:
            self.__trend = 'downtrend'
            self.temp_df = self.temp_df.loc[max_high_value:]
            first_row = self.temp_df.iloc[0]

            self.high = Point(first_row.name, first_row['High'])
            self.dynamic_low = Point(first_row.name, first_row['Low'])

            self.pivot_points.append(Point(self.high.datetime, self.high.price, ''))

        else:
            self.__trend = 'uptrend'
            self.temp_df = self.temp_df.loc[min_low_value:]
            first_row = self.temp_df.iloc[0]

            self.low = Point(first_row.name, first_row['Low'])
            self.dynamic_high = Point(first_row.name, first_row['High'])

            self.pivot_points.append(Point(self.low.datetime, self.low.price, ''))

    def find(self):
        self.__find_trend()
        rows_number = len(self.temp_df.index)

        while self.current_candle_index < rows_number:
            if self.__trend == 'downtrend':
                self.downtrend()
            else:
                self.uptrend()

    def plot_pivot_points(self, figure: go.Figure, marker_size: int = 7, color: str = 'black'):
        for point in self.pivot_points:
            point.plot(figure, color, marker_size)

    def plot_smc_levels(self, figure: go.Figure):
        for choch_bos in self.choches_and_boses:
            color = 'red' if choch_bos.name == 'CHoCH' else 'blue'
            choch_bos.plot(figure, color)

    def is_recent_high_exist(self):
        return self.high is not None

    def is_recent_low_exist(self):
        return self.low is not None

    def is_candle_closes_above_recent_high(self, candle: Candle):
        return self.is_recent_high_exist() and candle.close_price > self.high.price

    def is_candle_peak_above_recent_high(self, candle: Candle):
        return self.is_recent_high_exist() and candle.high_price > self.high.price

    def is_candle_closes_below_recent_low(self, candle: Candle):
        return self.is_recent_low_exist() and candle.close_price < self.low.price

    def is_candle_peak_below_recent_low(self, candle: Candle):
        return self.is_recent_low_exist() and candle.low_price < self.low.price

    def uptrend(self):
        for index, row in self.temp_df[self.current_candle_index:].iterrows():
            self.show_points()  ## ANIMATION

            # Convert df's row to candle
            candle = Candle(index, row)
            self.current_candle_index += 1

            if self.is_candle_closes_above_recent_high(candle):
                self.add_bos(self.high.datetime, candle.time, self.high.price)

            if self.is_candle_peak_above_recent_high(candle):
                self.low = Point(self.dynamic_low.datetime, self.dynamic_low.price)
                self.add_pivot_point(self.low, 'HL')

                self.dynamic_high = Point(candle.time, candle.high_price)
                self.high = None
                continue

            if self.is_candle_closes_below_recent_low(candle):
                self.add_choch(self.low.datetime, candle.time, self.low.price)
                self.low = None
                self.dynamic_low = Point(candle.time, candle.low_price)
                self.__trend = 'downtrend'

                if self.high is None:
                    self.high = Point(self.dynamic_high.datetime, self.dynamic_high.price)

                return

            #  Move-up dynamic high with the candle's high price
            if candle.high_price > self.dynamic_high.price:
                self.dynamic_high = Point(candle.time, candle.high_price)

                if not self.is_recent_high_exist() or self.dynamic_high.price < self.high.price:
                    self.dynamic_low = Point(candle.time, candle.low_price)

                continue

            # Move down dynamic low
            if self.dynamic_low is None or candle.low_price < self.dynamic_low.price:
                self.dynamic_low = Point(candle.time, candle.low_price)

            if self.is_recent_low_exist() and not self.is_recent_high_exist():
                swing_start = self.low
                swing_end = self.dynamic_high
                retracement_level = self.dynamic_low

                if self.retracement_verifier.is_valid(self.temp_df, swing_start, swing_end, retracement_level):
                    # Set new high and add HH pivot point
                    self.high = Point(self.dynamic_high.datetime, self.dynamic_high.price)
                    self.add_pivot_point(self.high, 'HH')

                    if self.animation_chart is not None:
                        fibonacci_retracement = FibonacciRetracement(swing_start, swing_end)
                        fibonacci_retracement.plot(self.animation_chart, swing_end.datetime)

    def downtrend(self):
        for index, row in self.temp_df[self.current_candle_index:].iterrows():
            self.show_points()  ## ANIMATION

            candle = Candle(index, row)
            self.current_candle_index += 1

            if self.is_candle_closes_below_recent_low(candle):
                self.add_bos(self.low.datetime, candle.time, self.low.price)

            if self.is_candle_peak_below_recent_low(candle):
                self.high = Point(self.dynamic_high.datetime, self.dynamic_high.price)
                self.add_pivot_point(self.high, 'LH')

                self.dynamic_low = Point(candle.time, candle.low_price)
                self.low = None
                continue

            if self.is_candle_closes_above_recent_high(candle):
                self.add_choch(self.high.datetime, candle.time, self.high.price)
                self.high = None
                self.dynamic_high = Point(candle.time, candle.high_price)
                self.__trend = 'uptrend'

                if self.low is None:
                    self.low = Point(self.dynamic_low.datetime, self.dynamic_low.price)

                return

            if candle.low_price < self.dynamic_low.price:
                self.dynamic_low = Point(candle.time, candle.low_price)

                if self.low is None or self.dynamic_low.price > self.low.price:
                    self.dynamic_high = Point(candle.time, candle.high_price)

                continue

            # Move up dynamic up
            if self.dynamic_high is None or candle.high_price > self.dynamic_high.price:
                self.dynamic_high = Point(candle.time, candle.high_price)

            # LL
            if self.is_recent_high_exist() and not self.is_recent_low_exist():
                swing_start = self.high
                swing_end = self.dynamic_low
                retracement_level = self.dynamic_high

                if self.retracement_verifier.is_valid(self.temp_df, swing_start, swing_end, retracement_level):
                    # Set new low and add LL pivot point
                    self.low = Point(self.dynamic_low.datetime, self.dynamic_low.price)
                    self.add_pivot_point(self.low, 'LL')

                    if self.animation_chart is not None:
                        fibonacci_retracement = FibonacciRetracement(swing_start, swing_end)
                        fibonacci_retracement.plot(self.animation_chart, swing_end.datetime)

    def add_pivot_point(self, point: Point, name: str):
        self.pivot_points.append(Point(point.datetime, point.price, name))

    def add_bos(self, start_x: datetime, end_x: datetime, y: float):
        SMC_LEVEL_TYPE = 'BOS'
        self.choches_and_boses.append(HorizontalTrendLine(SMC_LEVEL_TYPE, start_x, end_x, y))

    def add_choch(self, start_x: datetime, end_x: datetime, y: float):
        SMC_LEVEL_TYPE = 'CHoCH'
        self.choches_and_boses.append(HorizontalTrendLine(SMC_LEVEL_TYPE, start_x, end_x, y))

    def show_points(self):
        if self.animation_chart is None:
            return

        if self.dynamic_high:
            self.dynamic_high.plot(self.animation_chart, 'green', 10)

        if self.dynamic_low:
            self.dynamic_low.plot(self.animation_chart, 'red', 10)

        if self.high:
            self.high.plot(self.animation_chart, 'gray', 10)

        if self.low:
            self.low.plot(self.animation_chart, 'gray', 10)

        # Add pivot points and smc levels
        self.plot_pivot_points(self.animation_chart)
        self.plot_smc_levels(self.animation_chart)

        self.animation_chart.update_layout(showlegend=False, xaxis_rangeslider_visible=False)

        # Write image to file
        self.animation_chart.write_image(f'{IMAGES_FOLDER}/{self.animation_index}.png', format='png')
        self.animation_index += 1

        # Create new chart
        self.animation_chart = go.Figure(data=[go.Candlestick(x=self.df.index, open=self.df['Open'], high=self.df['High'], low=self.df['Low'], close=self.df['Close'])])

    def create_animation(self, output_video_path):
        images = [img for img in os.listdir(IMAGES_FOLDER) if img.endswith(".png")]
        images.sort(key=lambda x: int(x.split('.')[0]))  # Sort images based on numerical values

        frame = cv2.imread(os.path.join(IMAGES_FOLDER, images[0]))
        height, width, layers = frame.shape

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video = cv2.VideoWriter(output_video_path, fourcc, 1, (width, height))

        for image in images:
            img_path = os.path.join(IMAGES_FOLDER, image)
            frame = cv2.imread(img_path)
            video.write(frame)

        cv2.destroyAllWindows()
        video.release()

    def delete_and_create_folder(self, folder_path):
        # Delete the folder if it exists
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)  # Recursively remove the folder
                print(f"Deleted folder: {folder_path}")
            except Exception as e:
                print(f"Error deleting folder: {e}")

        # Create a new folder
        try:
            os.mkdir(folder_path)  # Create the folder
            print(f"Created folder: {folder_path}")
        except Exception as e:
            print(f"Error creating folder: {e}")

