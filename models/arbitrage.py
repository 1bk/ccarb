import datetime
from typing import Optional, Union

from pydantic import BaseModel


class ArbitrageDetails(BaseModel):
    crypto: str
    arbitrage_decision: str
    arbitrage_profit_amount: float
    arbitrage_profit_percent: float
    binance_btc_usdt: float
    luno_xbt_myr: float
    usd_myr: float
    btc_myr: float
    request_time: datetime.datetime = datetime.datetime.now()
    meta: Optional[Union[str, dict]]
