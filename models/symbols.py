from itertools import chain

from fastapi_utils.enums import StrEnum


class BinanceSymbols(StrEnum):
    ETHUSDT = "ETHUSDT"
    BTCUSDT = "BTCUSDT"


class LunoSymbols(StrEnum):
    XBTMYR = "XBTMYR"


class FiatSymbols(StrEnum):
    USDMYR = "USDMYR"


SupportedSymbols = StrEnum(
    "SupportedSymbols",
    [(i.name, i.value) for i in chain(FiatSymbols, BinanceSymbols, LunoSymbols)],
)
