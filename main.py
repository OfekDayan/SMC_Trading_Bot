import ccxt
import pandas as pd
import plotly.graph_objects as go
from MarketStructure.entry_zone_finder import EntryZoneFinder
from MarketStructure.pivot_points import PivotPoints
from TelegramHandler.telegram_handler import TelegramHandler
from smc.chart_methods import ChartMethods

# telegramHandler = TelegramHandler()
# telegramHandler.start()
#
# telegramHandler.send_message_to_user("", "C:\\Users\\ofekbiny\\Downloads\\newplot.png")
# poll_id = telegramHandler.send_poll_to_user()

# selection = telegramHandler.get_poll_response(poll_id)

symbol = 'BTCUSDT'
timeframe = '1h'

exchange = ccxt.binance()
exchange.options = {'defaultType': 'future', 'adjustForTimeDifference': True}

ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=700)
df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
df.set_index('Timestamp', inplace=True)

# create candlesticks chart
chart = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
# fig.update_layout(xaxis_rangeslider_visible=False, plot_bgcolor='black')

# For all candles, checks candle type & calculates it's imbalance value
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
entry_zone_finder.find(choches_and_boses, pivot_points)

chart.update_layout(xaxis_rangeslider_visible=False)
chart.show()
