import datetime
import threading
import ccxt
import dash
import pandas
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go
from DAL.DataAccessLayer import DatabaseManager
from signal_detector import SignalDetector
from MarketStructure.entry_zone_finder import EntryZoneFinder
from MarketStructure.pivot_points_detector import PivotPointsDetector
from Models.candle import Candle
from smc.chart_methods import ChartMethods
import telebot
from tools.order_block import OrderBlock
from user_options import UserOption

user_option_and_text = [
    (UserOption.TRADE, 'Take the trade!'),
    (UserOption.IGNORE, 'Ignore this signal'),
    (UserOption.NOTIFY_PRICE_HIT_ODB, 'Notify me when price hits the order block'),
    (UserOption.NOTIFY_REVERSAL_CANDLE_FOUND, 'Notify me if a reversal candle is found on Order Block')
    ]

DB_FILE_NAME = "SmcTradingBotDB.db"

# Telegram members
chat_id = 1451941685
BOT_ID = '5341091307:AAHGuAJDKLl3zzjIpfGhaVpW3Y3UgBNAXG4'
bot = telebot.TeleBot(BOT_ID)

# Dash app
app = dash.Dash(__name__)
chart_width_pixels = 800
chart_height_pixels = 600

app.layout = html.Div([
    dcc.Graph(id='candlestick-chart'),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,
        n_intervals=0,
        disabled=False
    ),
    html.Button('Freeze Chart', id='freeze-button', n_clicks=0),
    html.Button('Resume Chart', id='resume-button', n_clicks=0)
])


def get_candlestick_data_frame(symbol: str) -> pandas.DataFrame:
    TIME_FRAME = '1h'

    # Get the data frame from API
    exchange = ccxt.binance()
    exchange.options = {'defaultType': 'future', 'adjustForTimeDifference': True}
    candlestick_data = exchange.fetch_ohlcv(symbol, TIME_FRAME, limit=600)

    # Prepare data frame
    df = pd.DataFrame(candlestick_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)

    return df


def get_all_order_blocks(df: pandas.DataFrame, chart: go.Figure) -> list[(OrderBlock, pandas.DataFrame)]:
    """
        Gets all order blocks and their pullback dataframe
    """
    # For all candles, checks candle type & calculates its imbalance value
    chart_methods = ChartMethods(df)
    chart_methods.calculate_candles_patterns()
    chart_methods.calculate_imbalances(chart)

    # Find pivot points and SMC levels
    pivot_points_detector = PivotPointsDetector(df)
    pivot_points_detector.find()

    pivot_points_detector.plot_smc_levels(chart)
    pivot_points_detector.plot_pivot_points(chart)

    choches_and_boses = pivot_points_detector.choches_and_boses
    pivot_points = pivot_points_detector.pivot_points

    # Find order block and the corresponding pullback data frame
    entry_zone_finder = EntryZoneFinder(df, chart)
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


def handle_existing_order_blocks(chart: go.Figure, last_candle: Candle):
    db_manager = DatabaseManager(DB_FILE_NAME)
    active_order_blocks = db_manager.get_active_order_blocks()
    db_manager.close_connection()

    if not active_order_blocks:
        return

    for active_order_block in active_order_blocks:
        match active_order_block.user_decision:

            case UserOption.NOTIFY_PRICE_HIT_ODB.value:
                handle_price_hit_odb(active_order_block, last_candle, chart)

            case UserOption.NOTIFY_REVERSAL_CANDLE_FOUND.value:
                handle_reversal_candle_on_odb(active_order_block, last_candle, chart)


def handle_new_order_blocks(order_block: OrderBlock, pullback_zone_df: pandas.DataFrame, chart: go.Figure):
    # Signals finder
    signal_detector = SignalDetector(order_block, pullback_zone_df)
    is_to_send_signal = signal_detector.is_last_candle_reached_signal_price(chart)

    if is_to_send_signal:
        # Send notification to user
        image_path = "chart.jpg"
        chart.write_image(image_path, scale=4)
        poll_id = send_signal(image_path)

        # Get 90% fibo level if the user will choose in the future UserOption.NOTIFY_REVERSAL_CANDLE_FOUND
        order_block.ninty_percent_fibo_price = signal_detector.get_price_by_fib_level(90)

        # Insert order block to DB
        db_manager = DatabaseManager(DB_FILE_NAME)
        db_manager.insert_order_block(order_block, poll_id)
        db_manager.close_connection()


original_df = get_candlestick_data_frame('BTCUSDT')

starting_index = original_df.index.get_loc(datetime.datetime(2023, 7, 26, 19))

candle_counter = 0

lock = threading.Lock()


@app.callback(
    Output('interval-component', 'disabled'),
    Input('freeze-button', 'n_clicks'),
    Input('resume-button', 'n_clicks'),
    State('interval-component', 'disabled')
)
def update_chart_interval(freeze_clicks, resume_clicks, interval_disabled):
    # Determine which button was clicked last
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'freeze-button':
        # If the freeze button was clicked, disable the interval to freeze the chart updating
        return True
    elif button_id == 'resume-button':
        # If the resume button was clicked, enable the interval to resume the chart updating
        return False
    else:
        # If no button was clicked, keep the current state
        return interval_disabled


@app.callback(
    Output('candlestick-chart', 'figure'),
    Input('interval-component', 'n_intervals'),
    State('interval-component', 'disabled')
)
def update_chart(n, interval_disabled):
    global candle_counter

    if interval_disabled:
        # If the interval is disabled (chart frozen), return the current figure without updating
        return dash.no_update

    new_index = starting_index + candle_counter

    if new_index >= len(original_df):
        # Exit the while loop as the new index is greater than the maximum index
        return dash.no_update

    lock.acquire()

    df = original_df.iloc[:new_index]
    candle_counter += 1

    # create candlesticks chart
    chart = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])

    # Analyze
    results = get_all_order_blocks(df, chart)

    chart.update_layout(showlegend=False, xaxis_rangeslider_visible=False, width=chart_width_pixels, height=chart_height_pixels)

    # Check each order block
    for result in results:
        order_block = result[0]
        pullback_zone_df = result[1]

        # Plot
        order_block.plot(df, chart)

        # Handle
        handle_new_order_blocks(order_block, pullback_zone_df, chart)

    # Get last candle
    new_candle_row = df.tail(1).iloc[0]
    last_candle = Candle(new_candle_row.index[0], new_candle_row)

    # Handle existing order blocks
    handle_existing_order_blocks(chart, last_candle)

    lock.release()
    return chart


# Telegram BOT methods
def send_poll(question: str, options: list[str]):
    global chat_id
    return bot.send_poll(chat_id, question, options, is_anonymous=False)


def send_image(image_path: str, caption: str = None):
    global chat_id

    with open(image_path, 'rb') as image_file:
        bot.send_photo(chat_id, image_file, caption)


def send_signal(image_path: str):
    # Send the image
    send_image(image_path, "")

    # Send options poll
    options = [item[1] for item in user_option_and_text]
    return send_poll("what should I do?", options).poll.id


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
    # Get related order block
    db_manager = DatabaseManager(DB_FILE_NAME)
    related_order_block = db_manager.get_order_block_by_poll_id(pollAnswer.poll_id)

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
        db_manager.set_order_block_as_traded(related_order_block.id)
        db_manager.close_connection()


def bot_polling():
    bot.polling()


# @bot.message_handler()
# def start(message):
#     global chat_id
#     chat_id = message.chat.id


if __name__ == "__main__":
    bot_thread = threading.Thread(target=bot_polling)
    bot_thread.start()
    app.run_server(debug=False)
