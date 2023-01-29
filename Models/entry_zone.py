import pandas


class EntryZone:
    def __init__(self, df: pandas.DataFrame, is_bullish: bool):
        self.df = df
        self.is_bullish = is_bullish
