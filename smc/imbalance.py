from datetime import timedelta
from Models.candle import Candle
from tools.horizontal_trend_line import HorizontalTrendLine


def set_imbalances(df):
    df['Imbalance'] = 0

    df.loc[df['Close'] > df['Open'], 'Imbalance'] = df['Low'].shift(-1) - df['High'].shift(1)
    df.loc[df['Close'] > df['Open'], 'Imbalance_Start'] = df['Low'].shift(-1)
    df.loc[df['Close'] > df['Open'], 'Imbalance_End'] = df['High'].shift(1)

    df.loc[df['Open'] > df['Close'], 'Imbalance'] = df['Low'].shift(1) - df['High'].shift(-1)
    df.loc[df['Open'] > df['Close'], 'Imbalance_Start'] = df['High'].shift(-1)
    df.loc[df['Open'] > df['Close'], 'Imbalance_End'] = df['Low'].shift(1)

    df.loc[df['Imbalance'] < 0, 'Imbalance'] = 0

    return df


def plot_imbalances(figure, df):
    for index, row in df[1:].iterrows():
        if row['Imbalance'] > 0:
            from_time = index
            to_time = index + timedelta(hours=2)
            imbalance_start = row['Imbalance_Start']
            imbalance_end = row['Imbalance_End']

            candle = Candle(index, row)
            body_size = candle.body_size()
            imbalance_body_ratio = row['Imbalance'] / body_size

            if imbalance_body_ratio >= 0.5 and not candle.is_indecision():
                bottom_line = HorizontalTrendLine('', from_time, to_time, imbalance_start)
                top_line = HorizontalTrendLine('', from_time, to_time, imbalance_end)

                bottom_line.plot(figure, 'black')
                top_line.plot(figure, 'black')

    figure.update_layout(xaxis_rangeslider_visible=False)
    figure.show()
    pass

