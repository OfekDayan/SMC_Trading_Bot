import pandas
import yfinance as yf
import plotly.graph_objects as go
from MarketStructure.pivot_points import PivotPoints
import talib

from smc.imbalance import set_imbalances, plot_imbalances


def apply_candle(df: pandas.DataFrame, name: str, func) -> pandas.DataFrame:
    df[name] = func(df['Open'], df['High'], df['Low'], df['Close'])
    df[name] = df.apply(lambda x: True if x[name] == 100 or x[name] == -100 else False, axis=1)
    return df


ticker = 'MATIC-USD'
yfObj = yf.Ticker(ticker)
df = yfObj.history(period='20d', interval='1h')
df['type'] = df.apply(lambda x: 'Bullish' if x['Close'] > x['Open'] else 'Bearish', axis=1)

# Momentum
df = apply_candle(df, 'Marubozu', talib.CDLMARUBOZU)
df = apply_candle(df, 'Engulfing', talib.stream_CDLENGULFING)

# Indecision
df = apply_candle(df, 'Doji', talib.CDLDOJI)
df = apply_candle(df, 'Doji_Star', talib.stream_CDLDOJISTAR)
df = apply_candle(df, 'Dragonfly_Doji', talib.CDLDRAGONFLYDOJI)
df = apply_candle(df, 'Gravestone_Doji', talib.stream_CDLGRAVESTONEDOJI)
df = apply_candle(df, 'Long_Legged_Doji', talib.stream_CDLLONGLEGGEDDOJI)

df = apply_candle(df, 'Pinbar', talib.CDLHAMMER)

df = apply_candle(df, 'Inverted_Pinbar', talib.stream_CDLINVERTEDHAMMER)

df = apply_candle(df, 'Spinning_Top', talib.stream_CDLSPINNINGTOP)

df = apply_candle(df, 'Hanging_Man', talib.CDLHANGINGMAN)

df = apply_candle(df, 'Shooting_Star', talib.stream_CDLSHOOTINGSTAR)

fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
# fig.update_layout(xaxis_rangeslider_visible=False, plot_bgcolor='black')


df = set_imbalances(df)
plot_imbalances(fig, df)


pivot_points = PivotPoints(df)
pivot_points.find()
pivot_points.plot(fig)
