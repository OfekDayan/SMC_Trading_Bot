from enum import Enum


class UserOption(Enum):
    NONE = 0
    TRADE = 1
    IGNORE = 2
    NOTIFY_PRICE_HIT_ODB = 3
    NOTIFY_REVERSAL_CANDLE_FOUND = 4
