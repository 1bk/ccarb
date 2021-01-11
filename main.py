import asyncio
import datetime
from typing import Union

import fastapi
import httpx
import uvicorn
from codetiming import Timer
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
async def query_price(symbol: SupportedSymbols) -> CurrencyPair:
    timer = Timer(text=f"Task {symbol} elapsed time: {{:.1f}}")

    timer.start()
    price = 0
    if str(symbol) in list(BinanceSymbols):
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()

        price = resp.json().get("price")

    elif str(symbol) in list(LunoSymbols):
        url = f"https://api.luno.com/api/1/ticker?pair={symbol}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()

        price = resp.json().get("bid")


    elif str(symbol) in list(FiatSymbols):
        url = "https://api.exchangeratesapi.io/latest?base=USD&symbols=USD,MYR"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()

        price = resp.json().get("rates").get("MYR")

    timer.stop()
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
async def arbitrage(
        crypto: str = "BTC", trigger_percent: int = 3
) -> Union[ArbitrageDetails, fastapi.Response]:

    with Timer(text="\nTotal elapsed time: {:.1f}"):

        # Temporary
        if crypto.upper() != "BTC":
            return fastapi.Response(
                content="We only support `crypto=BTC` for now", status_code=501
            )

        pairs = await asyncio.gather(
            asyncio.create_task(query_price("USDMYR")),
            asyncio.create_task(query_price("BTCUSDT")),
            asyncio.create_task(query_price("XBTMYR")),
        )

        for p in pairs:
            if p.symbol == "USDMYR":
                usdmyr = p.price
            if p.symbol == "BTCUSDT":
                btcusdt = p.price
            if p.symbol == "XBTMYR":
                xbtmyr = p.price

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
        request_time=datetime.datetime.now(),
    )


if __name__ == "__main__":
    uvicorn.run(app, port=8111, host="127.0.0.1")
