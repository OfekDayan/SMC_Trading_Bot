import datetime
import threading
import ccxt
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go
from DecisionManager import DecisionManager
from MarketStructure.entry_zone_finder import EntryZoneFinder
from MarketStructure.pivot_points import PivotPoints
from smc.chart_methods import ChartMethods
import telebot

BOT_ID = '5341091307:AAHGuAJDKLl3zzjIpfGhaVpW3Y3UgBNAXG4'
bot = telebot.TeleBot(BOT_ID)

app = dash.Dash(__name__)

symbol = 'BTCUSDT'
timeframe = '1h'

starting_live_datetime = datetime.datetime(2023, 8, 1)

exchange = ccxt.binance()
exchange.options = {'defaultType': 'future', 'adjustForTimeDifference': True}
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=500)

original_df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
original_df['Timestamp'] = pd.to_datetime(original_df['Timestamp'], unit='ms')
original_df.set_index('Timestamp', inplace=True)

starting_index = original_df.index.get_loc(starting_live_datetime)
counter = 0

chat_id = 0

# Define the layout of the Dash app
app.layout = html.Div([
    dcc.Graph(id='candlestick-chart'),
    dcc.Interval(
        id='interval-component',
        interval=1*500,  # 1 second in milliseconds
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
        return go.Figure()

    df = original_df.iloc[:new_index]
    counter += 1

    # create candlesticks chart
    chart = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])

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
    results = entry_zone_finder.find(choches_and_boses, pivot_points)

    # Check each order block
    for result in results:
        order_block = result[0]
        pullback_zone_df = result[1]

        order_block.plot(df, chart)
        decision_manager = DecisionManager(order_block, pullback_zone_df)
        is_to_send_signal = decision_manager.is_to_send_signal()

        if is_to_send_signal:
            send_signal("C:\\Users\\ofekbiny\\Downloads\\newplot.png")

    chart.update_layout(xaxis_rangeslider_visible=False)
    return chart


def send_poll(question: str, options: list[str]):
    global chat_id
    bot.send_poll(chat_id, question, options, is_anonymous=False)


def send_image(image_path: str, caption: str = None):
    global chat_id

    with open(image_path, 'rb') as image_file:
        bot.send_photo(chat_id, image_file, caption)


@bot.message_handler()
def start(message):\
    # TODO: why global does not work?
    global chat_id
    chat_id = message.chat.id


def send_signal(image_path: str):
    send_image(image_path, "")

    options = ['Take the trade!',
               'Ignore this signal',
               'Notify me when price hits the order block',
               'Notify me when the liquidity will be taken',
               'Notify me if a reversal candle is found on Order Block']
    send_poll("what to do?", options)


@bot.poll_answer_handler()
def handle_poll_answer(pollAnswer):
    print(pollAnswer)


def bot_polling():
    bot.polling()


if __name__ == "__main__":
    bot_thread = threading.Thread(target=bot_polling)
    bot_thread.start()
    app.run_server(debug=True)
