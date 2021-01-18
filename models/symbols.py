from itertools import chain

from fastapi_utils.enums import StrEnum


class BinanceSymbols(StrEnum):
    ETHUSDT = "ETHUSDT"
    BTCUSDT = "BTCUSDT"
    ZENUSDT = "ZENUSDT"


class LunoSymbols(StrEnum):
    XBTMYR = "XBTMYR"
    ETHMYR = "ETHMYR"


class FiatSymbols(StrEnum):
    USDMYR = "USDMYR"


SupportedSymbols = StrEnum(
    "SupportedSymbols",
    [(i.name, i.value) for i in chain(FiatSymbols, BinanceSymbols, LunoSymbols)],
)
