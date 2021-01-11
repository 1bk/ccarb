import datetime
from typing import Optional, Union

from pydantic import BaseModel


class ArbitrageRequest(BaseModel):
    crypto: str = "BTC"
    target_percent: float = 3.0


class Arbitrage(BaseModel):
    decision: str
    profit_amount: float
    profit_percent: float


class ArbitrageDetails(BaseModel):
    crypto: str
    arbitrage: Arbitrage
    binance_btc_usdt: float
    luno_xbt_myr: float
    usd_myr: float
    btc_myr: float
    request_time: datetime.datetime
    meta: Optional[Union[str, dict]]
