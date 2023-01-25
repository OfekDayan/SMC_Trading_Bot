import yfinance as yf
import plotly.graph_objects as go
from MarketStructure.pivot_points import PivotPoints

# get data
from smc.chart_methods import ChartMethods

ticker = 'MATIC-USD'
yfObj = yf.Ticker(ticker)
df = yfObj.history(period='20d', interval='1h')
df['type'] = df.apply(lambda x: 'Bullish' if x['Close'] > x['Open'] else 'Bearish', axis=1)

# create candlesticks chart
fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
# fig.update_layout(xaxis_rangeslider_visible=False, plot_bgcolor='black')

chart_methods = ChartMethods(df)
chart_methods.calculate(fig)

# calculate pivot points
pivot_points = PivotPoints(df)
pivot_points.find()
pivot_points.add_to_chart(fig)

fig.update_layout(xaxis_rangeslider_visible=False)
fig.show()
