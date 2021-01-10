import datetime
from typing import Optional, Union

from pydantic import BaseModel

from models.symbols import SupportedSymbols


class CurrencyPair(BaseModel):
    symbol: SupportedSymbols
    price: float
    request_time: Optional[datetime.datetime]
    meta: Optional[Union[str, dict]]
