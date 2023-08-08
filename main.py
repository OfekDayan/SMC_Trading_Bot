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
from DecisionManager import DecisionManager
from MarketStructure.entry_zone_finder import EntryZoneFinder
from MarketStructure.pivot_points import PivotPoints
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

BOT_ID = '5341091307:AAHGuAJDKLl3zzjIpfGhaVpW3Y3UgBNAXG4'
bot = telebot.TeleBot(BOT_ID)

app = dash.Dash(__name__)

width_pixels = 800
height_pixels = 600

symbol = 'BTCUSDT'
timeframe = '1h'

exchange = ccxt.binance()
exchange.options = {'defaultType': 'future', 'adjustForTimeDifference': True}
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=500)

original_df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
original_df['Timestamp'] = pd.to_datetime(original_df['Timestamp'], unit='ms')
original_df.set_index('Timestamp', inplace=True)

counter = 0
chat_id = 1451941685
starting_live_datetime = datetime.datetime(2023, 8, 1)
starting_index = original_df.index.get_loc(starting_live_datetime)

# Define the layout of the Dash app
app.layout = html.Div([
    dcc.Graph(id='candlestick-chart'),
    dcc.Interval(
        id='interval-component',
        interval=1 * 500,
        n_intervals=0
    ),
    html.Button('Freeze Chart', id='freeze-button', n_clicks=0),
    html.Button('Resume Chart', id='resume-button', n_clicks=0)
])


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


def get_all_order_blocks(df: pandas.DataFrame, chart: go.Figure) -> list[(OrderBlock, pandas.DataFrame)]:
    """
        Gets all order blocks and their pullback dataframe
    """
    # For all candles, checks candle type & calculates its imbalance value
    chart_methods = ChartMethods(df)
    chart_methods.calculate(chart)

    # Find pivot points and CHOCH & BOS level
    pivot_points_finder = PivotPoints(df)
    pivot_points_finder.find()

    # Plot all
    pivot_points_finder.plot_smc_levels(chart)
    pivot_points_finder.plot_pivot_points(chart)

    choches_and_boses = pivot_points_finder.choches_and_boses
    pivot_points = pivot_points_finder.market_structure_points

    entry_zone_finder = EntryZoneFinder(df, chart)
    result = entry_zone_finder.find(choches_and_boses, pivot_points)
    return result


@app.callback(
    Output('candlestick-chart', 'figure'),
    Input('interval-component', 'n_intervals'),
    State('interval-component', 'disabled')
)
def update_chart(n, interval_disabled):
    global counter

    if interval_disabled:
        # If the interval is disabled (chart frozen), return the current figure without updating
        return dash.no_update

    new_index = starting_index + counter

    if new_index >= len(original_df):
        # Exit the while loop as the new index is greater than the maximum index
        return dash.no_update

    df = original_df.iloc[:new_index]
    counter += 1

    # create candlesticks chart
    chart = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])

    # Analyze
    results = get_all_order_blocks(df, chart)

    # Check each order block
    for result in results:
        order_block = result[0]
        pullback_zone_df = result[1]

        order_block.plot(df, chart)
        decision_manager = DecisionManager(order_block, pullback_zone_df)
        is_to_send_signal = decision_manager.is_to_send_signal(chart)

        chart.update_layout(showlegend=False, xaxis_rangeslider_visible=False, width=width_pixels, height=height_pixels)

        if is_to_send_signal:
            # Send notification to user
            image_path = "chart.jpg"
            chart.write_image(image_path, scale=4)
            send_signal(image_path)

            # Add order block to DB
            db_manager = DatabaseManager("SmcTradingBotDB.db")
            db_manager.insert_order_block(order_block)
            db_manager.close_connection()

    return chart


def send_poll(question: str, options: list[str]):
    global chat_id
    bot.send_poll(chat_id, question, options, is_anonymous=False)


def send_image(image_path: str, caption: str = None):
    global chat_id

    with open(image_path, 'rb') as image_file:
        bot.send_photo(chat_id, image_file, caption)

# @bot.message_handler()
# def start(message):
#     global chat_id
#     chat_id = message.chat.id


def send_signal(image_path: str):
    send_image(image_path, "")

    options = [item[1] for item in user_option_and_text]
    send_poll("what to do?", options)


@bot.poll_answer_handler()
def handle_poll_answer(pollAnswer):
    selected_option_index = pollAnswer.option_ids[0]
    selected_option = user_option_and_text[selected_option_index]
    pass


def bot_polling():
    bot.polling()


if __name__ == "__main__":
    bot_thread = threading.Thread(target=bot_polling)
    bot_thread.start()
    app.run_server(debug=False)
