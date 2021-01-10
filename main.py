import datetime as datetime
from itertools import chain
from typing import Optional, Union

import requests
import uvicorn
from fastapi import FastAPI
from fastapi_utils.enums import StrEnum
from pydantic import BaseModel

app = FastAPI()


class BinanceSymbols(StrEnum):
    ETHUSDT = 'ETHUSDT'
    BTCUSDT = 'BTCUSDT'


class LunoSymbols(StrEnum):
    XBTMYR = 'XBTMYR'


class FiatSymbols(StrEnum):
    USDMYR = 'USDMYR'


SupportedSymbols = StrEnum(
    'SupportedSymbols',
    [(i.name, i.value) for i in chain(FiatSymbols, BinanceSymbols, LunoSymbols)]
)


class CurrencyPair(BaseModel):
    symbol: str
    price: float
    request_time: Optional[datetime.datetime]
    meta: Union[str, dict]


class ArbitrageDetails(BaseModel):
    base: str
    usdmyr: float
    binance: float
    luno: float
    btcmyr: float
    request_time: datetime.datetime = datetime.datetime.now()
    arbitrage_decision: str
    arbitrage_profit: float
    meta: Optional[Union[str, dict]]


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/price/{symbol}")
def query_price(symbol: SupportedSymbols):
    price = None
    if str(symbol) in list(BinanceSymbols):
        response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
        price = response.json().get('price')
    elif str(symbol) in list(LunoSymbols):
        response = requests.get(f'https://api.luno.com/api/1/ticker?pair={symbol}')
        price = response.json().get('ask')
    elif str(symbol) in list(FiatSymbols):
        response = requests.get(f'https://api.exchangeratesapi.io/latest?base=USD&symbols=USD,MYR')
        price = response.json().get('rates').get('MYR')

    return {"symbol": symbol, "price": price}


@app.get("/arbitrage")
def arbitrage_details(base: str = 'BTC'):
    usdmyr = float(query_price('USDMYR').get('price'))
    btcusdt = float(query_price('BTCUSDT').get('price'))
    xbtmyr = float(query_price('XBTMYR').get('price'))

    btcmyr = btcusdt * usdmyr
    diff = xbtmyr - btcmyr

    if diff > 0:
        arbitrage_decision = 'Buy in Binance, Sell in Luno'
        arbitrage_profit = diff
    elif diff < 0:
        arbitrage_decision = 'Buy in Luno, Sell in Binance'
        arbitrage_profit = -diff
    else:
        arbitrage_decision = 'No decision'
        arbitrage_profit = 0

    return ArbitrageDetails(
        base=base,
        usdmyr=usdmyr,
        binance=usdmyr,
        luno=xbtmyr,
        btcmyr=btcmyr,
        arbitrage_decision=arbitrage_decision,
        arbitrage_profit=arbitrage_profit,
    )



if __name__ == '__main__':
    uvicorn.run(app, port=8111, host="127.0.0.1")
