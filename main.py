from typing import Union

import fastapi
import requests
import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse, Response

from models.arbitrage import ArbitrageDetails
from models.currancy_pair import CurrencyPair
from models.symbols import SupportedSymbols, BinanceSymbols, LunoSymbols, FiatSymbols

app = FastAPI()


@app.get("/")
def read_root():
    return {
        "AppName": "CryptoCurrency Arbitrage",
        "Message": "Hello there! Go to site path: /arb",
    }


@app.get("/price/{symbol}", response_model=CurrencyPair)
def query_price(symbol: SupportedSymbols) -> CurrencyPair:
    price = None
    if str(symbol) in list(BinanceSymbols):
        response = requests.get(
            f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        )
        price = response.json().get("price")
    elif str(symbol) in list(LunoSymbols):
        response = requests.get(f"https://api.luno.com/api/1/ticker?pair={symbol}")
        price = response.json().get("ask")
    elif str(symbol) in list(FiatSymbols):
        response = requests.get(
            "https://api.exchangeratesapi.io/latest?base=USD&symbols=USD,MYR"
        )
        price = response.json().get("rates").get("MYR")

    return CurrencyPair(
        symbol=symbol,
        price=float(price),
    )


@app.get(
    "/arb", name="redirects_to_arbitrage", status_code=307, response_class=Response
)
def arb():
    response = RedirectResponse("/arbitrage")
    return response


@app.get(
    "/arbitrage", name="determine_arbitrage_details", response_model=ArbitrageDetails
)
def arbitrage(
    crypto: str = "BTC", trigger_percent: int = 3
) -> Union[ArbitrageDetails, fastapi.Response]:
    # Temporary
    if crypto.upper() != "BTC":
        return fastapi.Response(
            content="We only support `crypto=BTC` for now", status_code=501
        )

    usdmyr = query_price("USDMYR").price
    btcusdt = query_price("BTCUSDT").price
    xbtmyr = query_price("XBTMYR").price

    btcmyr = btcusdt * usdmyr
    diff = xbtmyr - btcmyr
    perc = abs(diff) / max(xbtmyr, btcmyr) * 100

    if diff > 0 and perc > trigger_percent:
        arbitrage_decision = "Buy in Binance, Sell in Luno"
        arbitrage_profit_amount = diff
        arbitrage_profit_percent = diff / xbtmyr * 100
    elif diff < 0 and perc > trigger_percent:
        arbitrage_decision = "Buy in Luno, Sell in Binance"
        arbitrage_profit_amount = -diff
        arbitrage_profit_percent = diff / btcmyr * 100
    else:
        arbitrage_decision = "No decision!"
        arbitrage_profit_amount = abs(diff)
        arbitrage_profit_percent = perc

    return ArbitrageDetails(
        crypto=crypto,
        arbitrage_decision=arbitrage_decision,
        arbitrage_profit_amount=arbitrage_profit_amount,
        arbitrage_profit_percent=arbitrage_profit_percent,
        binance_btc_usdt=btcusdt,
        luno_xbt_myr=xbtmyr,
        usd_myr=usdmyr,
        btc_myr=btcmyr,
    )


if __name__ == "__main__":
    uvicorn.run(app, port=8111, host="127.0.0.1")
