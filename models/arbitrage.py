import datetime
from typing import Optional, Union

from fastapi_utils.enums import StrEnum
from pydantic import BaseModel


class ValidCrypto(StrEnum):
    BTC = "BTC"
    # ETH = "ETH"   # WIP


class ArbitrageRequest(BaseModel):
    crypto: ValidCrypto = ValidCrypto.BTC
    target_percent: float = 3.0


class Arbitrage(BaseModel):
    decision: str
    profit_amount: float
    profit_percent: float


class ArbitrageDetails(BaseModel):
    request: ArbitrageRequest
    arbitrage: Arbitrage
    binance_btc_usdt: float
    luno_xbt_myr: float
    usd_myr: float
    btc_myr: float
    request_time: datetime.datetime
    meta: Optional[Union[str, dict]]
