import ccxt
import pandas as pd
import plotly.graph_objects as go
from MarketStructure.entry_zone_finder import EntryZoneFinder
from MarketStructure.pivot_points import PivotPoints
from smc.chart_methods import ChartMethods

symbol = 'BTCUSDT'
timeframe = '15m'

exchange = ccxt.binance()
exchange.options = {'defaultType': 'future', 'adjustForTimeDifference': True}

ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=500)
df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
df.set_index('Timestamp', inplace=True)

# create candlesticks chart
fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
# fig.update_layout(xaxis_rangeslider_visible=False, plot_bgcolor='black')

chart_methods = ChartMethods(df)
# chart_methods.calculate(fig)
chart_methods.calculate()

# calculate pivot points
pivot_points = PivotPoints(df)
pivot_points.find()
pivot_points.add_to_chart(fig)

entry_zone_finder = EntryZoneFinder(df, fig)
entry_zone_finder.find(pivot_points.choches_and_boses, pivot_points.market_structure_points)

fig.update_layout(xaxis_rangeslider_visible=False)
fig.show()
