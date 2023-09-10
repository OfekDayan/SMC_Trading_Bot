import datetime
import os.path
import threading
import ccxt
import dash
import pandas
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go
import webbrowser
from DAL.DataAccessLayer import DatabaseManager
from constants import Constants
from signal_detector import SignalDetector
from MarketStructure.entry_zone_finder import EntryZoneFinder
from MarketStructure.pivot_points_detector import PivotPointsDetector
from Models.candle import Candle
from smc.chart_methods import ChartMethods
import telebot
from tools.order_block import OrderBlock, OrderBlockStatus
from user_options import UserOption
from PIL import Image

user_option_and_text = [
    (UserOption.TRADE, 'Take the trade!'),
    (UserOption.IGNORE, 'Ignore this signal'),
    (UserOption.NOTIFY_PRICE_HIT_ODB, 'Notify me when price hits the order block'),
    (UserOption.NOTIFY_REVERSAL_CANDLE_FOUND, 'Notify me if a reversal candle is found on Order Block')
    ]

chart_contexts = []
symbols = []

optional_timeframes = ['1m', '5m', '15m', '30m', '1h', '1d']
optional_coins = ['BTC', 'ETH', 'MATIC', 'SAND', 'LTC', 'BNB', 'SOL', 'ADA', 'DOT', 'DOGE']

DB_FILE_NAME = "SmcTradingBotDB.db"

user_answer_poll_event = threading.Event()

# Telegram members
chat_id = 1451941685
BOT_ID = '5341091307:AAHGuAJDKLl3zzjIpfGhaVpW3Y3UgBNAXG4'
bot = telebot.TeleBot(BOT_ID)

# Dash app
INTERVAL = 3000
NUMBER_OF_CANDLES = 400
app = dash.Dash(__name__)
chart_width_pixels = 800
chart_height_pixels = 1200

start_date_to_run_live_candles = datetime.datetime(2023, 9, 5)

PIVOT_POINTS_SIMULATOR = False
is_to_update_symbols = True


def get_coin_image_path(symbol: str):
    EXTENSION = 'png'
    IMAGES_FOLDER_PATH = 'coins_images'
    coin = symbol.replace('USDT', '').lower()
    path = os.path.join(IMAGES_FOLDER_PATH, f'{coin}.{EXTENSION}')
    return Image.open(path)


def slice_list_by_timestamp_range(main_list, start_timestamp, end_timestamp):
    sliced_list = []
    for sublist in main_list:
        timestamp = sublist[0]
        if start_timestamp <= timestamp / 1000 <= end_timestamp:
            sliced_list.append(sublist)
    return sliced_list


def write_df(symbol: str, candlestick_data):
    # Slice the DataFrame using loc
    start_date = int(pd.Timestamp(datetime.datetime(2022, 11, 8, 0, 0, 0)).timestamp())
    end_date = int(pd.Timestamp(datetime.datetime(2023, 5, 15, 0, 0, 0)).timestamp())
    candlestick_data_to_write = slice_list_by_timestamp_range(candlestick_data, start_date, end_date)

    file_name = f"dataframes\\{symbol}_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"

    with open(file_name, 'w') as file:
        file.write(Constants.time_frame + '\n')  # timeframe
        file.write('2023-03-13 00:00:00\n')      # start live running

        # Date
        for item in candlestick_data_to_write:
            file.write(str(item) + '\n')


def read_df(path):
    candlestick_data = []

    lines = []
    with open(path, 'r') as file:
        for line in file:
            lines.append(line)

    timeframe = lines[0].rstrip('\n')
    start_live_running = datetime.datetime.strptime(lines[1].rstrip('\n'), "%Y-%m-%d %H:%M:%S")

    for line in lines[2:]:
        line = line.strip().replace('[', '').replace(']', '').split(',')
        line_as_floats = [float(item) for item in line]
        candlestick_data.append(line_as_floats)

    df = pd.DataFrame(candlestick_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)

    return df, timeframe, start_live_running



def get_candlestick_data_frame(symbol: str) -> pandas.DataFrame:
    timeframe = Constants.time_frame
    start_live_running = start_date_to_run_live_candles

    # Get the data frame from API
    exchange = ccxt.binance()
    exchange.options = {'defaultType': 'future', 'adjustForTimeDifference': True}
    candlestick_data = exchange.fetch_ohlcv(symbol, Constants.time_frame, limit=NUMBER_OF_CANDLES)

    df = pd.DataFrame(candlestick_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)

    if symbol == "LTCUSDT":
        pass
        # write_df(symbol, candlestick_data)
        # return read_df("dataframes\LTCUSDT_20230911022725.txt")

    return df, timeframe, start_live_running


def get_all_order_blocks(df: pandas.DataFrame, symbol: str, chart: go.Figure, timeframe) -> list[(OrderBlock, pandas.DataFrame)]:
    """
        Gets all order blocks and their pullback dataframe
    """
    # For all candles, checks candle type & calculates its imbalance value
    chart_methods = ChartMethods(df, timeframe)
    chart_methods.calculate_candles_patterns()
    chart_methods.calculate_imbalances(chart)
    chart_methods.calculate_big_candles()

    # Find pivot points and SMC levels
    pivot_points_detector = PivotPointsDetector(df, timeframe)
    pivot_points_detector.find()

    pivot_points_detector.plot_smc_levels(chart)
    pivot_points_detector.plot_pivot_points(chart)

    choches_and_boses = pivot_points_detector.choches_and_boses
    pivot_points = pivot_points_detector.pivot_points

    # Find order block and the corresponding pullback data frame
    entry_zone_finder = EntryZoneFinder(df, chart, symbol, timeframe)
    result = entry_zone_finder.find(choches_and_boses, pivot_points)

    return result


def handle_price_hit_odb(order_block: OrderBlock, last_candle: Candle, chart: go.Figure):
    is_price_hits_odb = last_candle.low_price <= order_block.top_right.price if \
        order_block.is_bullish else last_candle.high_price >= order_block.bottom_left.price

    if is_price_hits_odb:
        # Send notification - trade or ignore
        image_path = "chart.jpg"
        chart.write_image(image_path, scale=4)
        poll_id = send_price_hit_odb_signal(image_path)

        # Update the poll id and user decision
        db_manager = DatabaseManager(DB_FILE_NAME)
        db_manager.update_poll_id(order_block.id, poll_id)
        db_manager.update_user_decision(order_block.id, UserOption.NONE)
        db_manager.close_connection()


def handle_reversal_candle_on_odb(order_block: OrderBlock, last_candle: Candle, chart: go.Figure):
    # Check is the closing price of the candle is between the 90% fibo price to the end price of the ODB
    ninty_percent_fibo_price = order_block.ninty_percent_fibo_price

    is_candle_in_checking_range = order_block.bottom_left.price <= last_candle.close_price <= ninty_percent_fibo_price \
        if order_block.is_bullish else ninty_percent_fibo_price <= last_candle.close_price <= order_block.top_right.price

    if is_candle_in_checking_range and last_candle.is_reversal():
        image_path = "chart.jpg"
        chart.write_image(image_path, scale=4)
        candle_type = last_candle.get_candle_type()
        poll_id = send_reversal_candle_found_on_odb_signal(image_path, candle_type)

        # Update the poll id and user decision
        db_manager = DatabaseManager(DB_FILE_NAME)
        db_manager.update_poll_id(order_block.id, poll_id)
        db_manager.update_user_decision(order_block.id, UserOption.NONE)
        db_manager.close_connection()


def handle_existing_order_blocks(symbol: str, chart: go.Figure, last_candle: Candle):
    db_manager = DatabaseManager(DB_FILE_NAME)
    active_order_blocks = db_manager.get_active_order_blocks(symbol)
    db_manager.close_connection()

    if not active_order_blocks:
        return

    for active_order_block in active_order_blocks:
        match active_order_block.user_decision:

            case UserOption.NOTIFY_PRICE_HIT_ODB.value:
                handle_price_hit_odb(active_order_block, last_candle, chart)

            case UserOption.NOTIFY_REVERSAL_CANDLE_FOUND.value:
                handle_reversal_candle_on_odb(active_order_block, last_candle, chart)


def freeze_symbol_updating(symbol: str):
    for chart_context in chart_contexts:
        if chart_context[0] == symbol:
            chart_context[5] = False
            break


def resume_symbol_updating(symbol: str):
    for chart_context in chart_contexts:
        if chart_context[0] == symbol:
            chart_context[5] = True
            break


def handle_new_order_blocks(order_block: OrderBlock, pullback_zone_df: pandas.DataFrame, chart: go.Figure, timeframe):
    # Signals finder
    signal_detector = SignalDetector(order_block, pullback_zone_df, timeframe)
    is_to_send_signal = signal_detector.is_last_candle_reached_signal_price(chart)

    if is_to_send_signal:
        # Freeze updating
        freeze_symbol_updating(order_block.symbol)

        # Send notification to user
        image_path = "chart.jpg"
        chart.write_image(image_path, scale=4)
        poll_id = send_signal(image_path, order_block.symbol)

        # Get 90% fibo level if the user will choose in the future UserOption.NOTIFY_REVERSAL_CANDLE_FOUND
        order_block.ninty_percent_fibo_price = signal_detector.get_price_by_fib_level(90)

        # Insert order block to DB
        db_manager = DatabaseManager(DB_FILE_NAME)
        db_manager.insert_order_block(order_block, poll_id)
        db_manager.close_connection()


def get_updated_chart(interval_disabled, symbol: str, df: pandas.DataFrame, candles_counter: int, start_date_to_run_live_candles, is_to_run, timeframe) -> go.Figure:
    if interval_disabled or not is_to_run:
        # If the interval is disabled (chart frozen), return the current figure without updating
        return dash.no_update

    start_candles_index = df.index.get_loc(start_date_to_run_live_candles, method='nearest')
    new_index = start_candles_index + candles_counter

    if new_index >= len(df):
        # Exit the while loop as the new index is greater than the maximum index
        return dash.no_update

    df = df.iloc[:new_index]

    # create candlesticks chart
    chart = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])

    # Analyze
    results = get_all_order_blocks(df, symbol, chart, timeframe)

    chart.update_layout(showlegend=False, xaxis_rangeslider_visible=False, height=chart_height_pixels, width=chart_width_pixels)

    # Check each order block
    for result in results:
        order_block = result[0]
        pullback_zone_df = result[1]

        # Plot
        order_block.plot(df, chart)

        # Handle
        handle_new_order_blocks(order_block, pullback_zone_df, chart, timeframe)

    # Get last candle
    new_candle_row = df.tail(1).iloc[0]
    last_candle = Candle(new_candle_row.index[0], new_candle_row, timeframe)

    # Handle existing order blocks
    handle_existing_order_blocks(symbol, chart, last_candle)

    return chart


def update_chart_by_context_index(context_index: int, interval_disabled: bool):
    chart_context = chart_contexts[context_index]

    symbol = chart_context[0]
    df = chart_context[1]
    start_date_to_run_live_candles = chart_context[2]
    candles_counter = chart_context[3]
    pad_lock = chart_context[4]
    is_to_run = chart_context[5]
    timeframe = chart_context[6]

    pad_lock.acquire()
    updated_chart = get_updated_chart(interval_disabled, symbol, df, candles_counter, start_date_to_run_live_candles, is_to_run, timeframe)
    chart_context[3] += 1
    pad_lock.release()

    return updated_chart


def pivot_points_simulator(symbol: str):
    df = get_candlestick_data_frame(symbol)
    chart_methods = ChartMethods(df)
    chart_methods.calculate_candles_patterns()
    chart_methods.calculate_imbalances()
    chart_methods.calculate_big_candles()

    # Find pivot points and SMC levels
    pivot_points_detector = PivotPointsDetector(df, True)
    pivot_points_detector.find()
    pivot_points_detector.create_animation("animation.avi")


if PIVOT_POINTS_SIMULATOR:
    pivot_points_simulator('MATICUSDT')
    exit(0)


# Telegram BOT methods
def send_poll(question: str, options: list[str]):
    global chat_id
    return bot.send_poll(chat_id, question, options, is_anonymous=False)


def send_poll_multiple_answers(question: str, options: list[str]):
    global chat_id
    return bot.send_poll(chat_id, question, options, allows_multiple_answers=True, is_anonymous=False)


def send_image(image_path: str, caption: str = None):
    global chat_id

    with open(image_path, 'rb') as image_file:
        bot.send_photo(chat_id, image_file, caption)


def send_signal(image_path: str, symbol: str):
    # Send the image
    send_image(image_path, "")

    # Send options poll
    options = [item[1] for item in user_option_and_text]
    return send_poll(f"what should I do ({symbol})?", options).poll.id


def send_second_signal(image_path: str, message: str):
    # Send the image
    send_image(image_path, "")

    # Send options poll - TRADE / IGNORE
    options = [user_option_and_text[0][1], user_option_and_text[1][1]]
    return send_poll(message, options).poll.id


def send_price_hit_odb_signal(image_path: str):
    MESSAGE_TO_SEND = "I'm notifying you that the price hit's the order block - what should I do?"
    return send_second_signal(image_path, MESSAGE_TO_SEND)


def send_reversal_candle_found_on_odb_signal(image_path: str, candle_type):
    MESSAGE_TO_SEND = f"I'm notifying you that the I found a reversal candle ({candle_type}) on the order block - what should I do?"
    return send_second_signal(image_path, MESSAGE_TO_SEND)


@bot.poll_answer_handler()
def handle_poll_answer(pollAnswer):
    poll_id = pollAnswer.poll_id

    # Coins selection poll
    if poll_id == coins_selection_poll_id:
        for i in pollAnswer.option_ids:
            coin = optional_coins[i]
            symbols.append(f'{coin.upper()}USDT')

        # Signal the main thread that the user selected coins
        user_answer_poll_event.set()
        return

    # Timeframe selection poll
    if poll_id == timeframe_selection_poll_id:
        index = pollAnswer.option_ids[0]
        Constants.time_frame = optional_timeframes[index]
        # Signal the main thread that the user selected timeframe
        user_answer_poll_event.set()
        return

    # Get related order block
    db_manager = DatabaseManager(DB_FILE_NAME)
    related_order_block = db_manager.get_order_block_by_poll_id(poll_id)

    # Get selected option
    selected_option_index = pollAnswer.option_ids[0]
    user_decision = user_option_and_text[selected_option_index][0]

    # Update order block's user decision in DB
    db_manager.update_user_decision(related_order_block.id, user_decision)
    db_manager.close_connection()

    # Handle TRADE response
    if user_decision == UserOption.TRADE:
        # TODO: take the trade - market - ccxt

        # Update order block in DB to be considered as traded
        db_manager = DatabaseManager(DB_FILE_NAME)
        db_manager.update_status(related_order_block.id, OrderBlockStatus.TRADING)
        db_manager.close_connection()

    # Resume symbol updating
    resume_symbol_updating(related_order_block.symbol)


def bot_polling():
    bot.polling()
    pass


# @bot.message_handler()
# def start(message):
#     pass


app.layout = html.Div([
    html.Div([
        html.Div([
            html.Img(id='image1', style={'height': '50px', 'margin-right': '10px'}),
            html.H3(id='label1', children="Label 1", style={'color': '#333', 'font-size': '28px', 'font-weight': 'bold',
                                                            'font-family': 'Arial, sans-serif'}),
            dcc.Graph(id='candlestick-chart1'),
        ], style={'flex': '1', 'margin': '10px', 'padding': '20px', 'background-color': '#f5f5f5',
                  'border-radius': '10px', 'box-shadow': '0 0 10px rgba(0, 0, 0, 0.1)'}),

        html.Div([
            html.Img(id='image2', style={'height': '50px', 'margin-right': '10px'}),
            html.H3(id='label2', children="Label 2", style={'color': '#333', 'font-size': '28px', 'font-weight': 'bold',
                                                            'font-family': 'Arial, sans-serif'}),
            dcc.Graph(id='candlestick-chart2'),
        ], style={'flex': '1', 'margin': '10px', 'padding': '20px', 'background-color': '#f5f5f5',
                  'border-radius': '10px', 'box-shadow': '0 0 10px rgba(0, 0, 0, 0.1)'}),
    ], style={'display': 'flex', 'justify-content': 'center'}),

    html.Div([
        html.Div([
            html.Img(id='image3', style={'height': '50px', 'margin-right': '10px'}),
            html.H3(id='label3', children="Label 3", style={'color': '#333', 'font-size': '28px', 'font-weight': 'bold',
                                                            'font-family': 'Arial, sans-serif'}),
            dcc.Graph(id='candlestick-chart3'),
        ], style={'flex': '1', 'margin': '10px', 'padding': '20px', 'background-color': '#f5f5f5',
                  'border-radius': '10px', 'box-shadow': '0 0 10px rgba(0, 0, 0, 0.1)'}),

        html.Div([
            html.Img(id='image4', style={'height': '50px', 'margin-right': '10px'}),
            html.H3(id='label4', children="Label 4", style={'color': '#333', 'font-size': '28px', 'font-weight': 'bold',
                                                            'font-family': 'Arial, sans-serif'}),
            dcc.Graph(id='candlestick-chart4'),
        ], style={'flex': '1', 'margin': '10px', 'padding': '20px', 'background-color': '#f5f5f5',
                  'border-radius': '10px', 'box-shadow': '0 0 10px rgba(0, 0, 0, 0.1)'}),
    ], style={'display': 'flex', 'justify-content': 'center'}),

    dcc.Interval(
        id='interval1',
        interval=1 * INTERVAL,
        n_intervals=0,
        disabled=False
    ),

    dcc.Interval(
        id='interval2',
        interval=1 * INTERVAL,
        n_intervals=0,
        disabled=False
    ),

    dcc.Interval(
        id='interval3',
        interval=1 * INTERVAL,
        n_intervals=0,
        disabled=False
    ),

    dcc.Interval(
        id='interval4',
        interval=1 * INTERVAL,
        n_intervals=0,
        disabled=False
    ),

    dcc.Interval(
        id='labels_interval',
        interval=1 * INTERVAL,
        n_intervals=0,
        disabled=False
    ),
    # html.Button('Freeze Chart', id='freeze-button', n_clicks=0),
    # html.Button('Resume Chart', id='resume-button', n_clicks=0)
])


# @app.callback(
#     Output('interval1', 'disabled'),
#     Input('freeze-button', 'n_clicks'),
#     Input('resume-button', 'n_clicks'),
#     State('interval1', 'disabled')
# )
# def update_chart_interval(freeze_clicks, resume_clicks, interval_disabled):
#     # Determine which button was clicked last
#     ctx = dash.callback_context
#     button_id = ctx.triggered[0]['prop_id'].split('.')[0]
#
#     if button_id == 'freeze-button':
#         # If the freeze button was clicked, disable the interval to freeze the chart updating
#         return True
#     elif button_id == 'resume-button':
#         # If the resume button was clicked, enable the interval to resume the chart updating
#         return False
#     else:
#         # If no button was clicked, keep the current state
#         return interval_disabled


@app.callback(
    [Output('label1', 'children'),
     Output('label2', 'children'),
     Output('label3', 'children'),
     Output('label4', 'children'),
     Output('image1', 'src'),
     Output('image2', 'src'),
     Output('image3', 'src'),
     Output('image4', 'src')],
    [Input('labels_interval', 'n_intervals')]  # Use any suitable input trigger
)
def update_labels(n_intervals):
    global is_to_update_symbols

    if is_to_update_symbols:
        # Your logic to update label text dynamically
        symbol1 = chart_contexts[0][0]
        symbol2 = chart_contexts[1][0]
        symbol3 = chart_contexts[2][0]
        symbol4 = chart_contexts[3][0]

        symbol1_image_path = get_coin_image_path(symbol1)
        symbol2_image_path = get_coin_image_path(symbol2)
        symbol3_image_path = get_coin_image_path(symbol3)
        symbol4_image_path = get_coin_image_path(symbol4)

        is_to_update_symbols = False

        return symbol1, symbol2, symbol3, symbol4, symbol1_image_path, symbol2_image_path, symbol3_image_path, symbol4_image_path

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    Output('candlestick-chart1', 'figure'),
    Input('interval1', 'n_intervals'),
    State('interval1', 'disabled')
)
def update_chart(n, interval_disabled):
    CHART_CONTEXT_INDEX = 0
    return update_chart_by_context_index(CHART_CONTEXT_INDEX, interval_disabled)


@app.callback(
    Output('candlestick-chart2', 'figure'),
    Input('interval2', 'n_intervals'),
    State('interval2', 'disabled')
)
def update_chart(n, interval_disabled):
    CHART_CONTEXT_INDEX = 1
    return update_chart_by_context_index(CHART_CONTEXT_INDEX, interval_disabled)


@app.callback(
    Output('candlestick-chart3', 'figure'),
    Input('interval3', 'n_intervals'),
    State('interval3', 'disabled')
)
def update_chart(n, interval_disabled):
    CHART_CONTEXT_INDEX = 2
    return update_chart_by_context_index(CHART_CONTEXT_INDEX, interval_disabled)


@app.callback(
    Output('candlestick-chart4', 'figure'),
    Input('interval4', 'n_intervals'),
    State('interval4', 'disabled')
)
def update_chart(n, interval_disabled):
    CHART_CONTEXT_INDEX = 3
    return update_chart_by_context_index(CHART_CONTEXT_INDEX, interval_disabled)


if __name__ == "__main__":
    bot_thread = threading.Thread(target=bot_polling)
    bot_thread.start()

    # Ask user which coins to monitor
    coins_selection_poll_id = send_poll_multiple_answers("Please choose 4 coins to monitor", optional_coins).poll.id
    # Wait for response
    user_answer_poll_event.wait()

    user_answer_poll_event.clear()

    # Ask user which coins to monitor
    timeframe_selection_poll_id = send_poll("Please select time frame to monitor", optional_timeframes).poll.id
    # Wait for response
    user_answer_poll_event.wait()

    for symbol in symbols:
        candles_counter = 0
        pad_lock = threading.Lock()
        df, timeframe, start_live_running = get_candlestick_data_frame(symbol)
        is_to_run = True
        chart_contexts.append([symbol, df, start_live_running, candles_counter, pad_lock, is_to_run, timeframe])

    webbrowser.open_new("http://127.0.0.1:8050/")
    app.run_server(debug=False)
