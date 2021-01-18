import asyncio
import datetime
from typing import Union

import fastapi
import httpx
import pandas as pd
import uvicorn
from codetiming import Timer
from fastapi import FastAPI, Depends
from starlette.responses import RedirectResponse, Response

from models.arbitrage import ArbitrageDetails, Arbitrage, ArbitrageRequest
from models.currancy_pair import CurrencyPair
from models.symbols import SupportedSymbols, BinanceSymbols, LunoSymbols, FiatSymbols
from service.zennode import get_zen_node_payments, SecureNodePayments

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
    if symbol in list(BinanceSymbols):
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()

        price = resp.json().get("price")

    elif symbol in list(LunoSymbols):
        url = f"https://api.luno.com/api/1/ticker?pair={symbol}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()

        price = resp.json().get("bid")

    elif symbol in list(FiatSymbols):
        url = "https://api.exchangeratesapi.io/latest?base=USD&symbols=USD,MYR"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()

        price = resp.json().get("rates").get("MYR")

    timer.stop()
    return CurrencyPair(
        symbol=symbol,
        price=float(price),
        request_time=datetime.datetime.now(),
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
    arbitrage_request: ArbitrageRequest = Depends(),
) -> Union[ArbitrageDetails, fastapi.Response]:
    with Timer(text="\nTotal elapsed time: {:.1f}"):

        # Temporary
        if arbitrage_request.crypto.upper() != "BTC":
            return fastapi.Response(
                content="We only support `crypto=BTC` for now", status_code=501
            )

        pairs = await asyncio.gather(
            asyncio.create_task(query_price(FiatSymbols.USDMYR)),
            asyncio.create_task(query_price(BinanceSymbols.BTCUSDT)),
            asyncio.create_task(query_price(LunoSymbols.XBTMYR)),
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

        if diff > 0 and perc > arbitrage_request.target_percent:
            arbitrage_decision = "Buy in Binance, Sell in Luno"
            arbitrage_profit_amount = diff
            arbitrage_profit_percent = diff / xbtmyr * 100
        elif diff < 0 and perc > arbitrage_request.target_percent:
            arbitrage_decision = "Buy in Luno, Sell in Binance"
            arbitrage_profit_amount = -diff
            arbitrage_profit_percent = diff / btcmyr * 100
        else:
            arbitrage_decision = "No decision!"
            arbitrage_profit_amount = abs(diff)
            arbitrage_profit_percent = perc

    return ArbitrageDetails(
        request=arbitrage_request,
        arbitrage=Arbitrage(
            decision=arbitrage_decision,
            profit_amount=arbitrage_profit_amount,
            profit_percent=arbitrage_profit_percent,
        ),
        binance_btc_usdt=btcusdt,
        luno_xbt_myr=xbtmyr,
        usd_myr=usdmyr,
        btc_myr=btcmyr,
        request_time=datetime.datetime.now(),
    )


@app.get("/zennode", name="determine_secure_node_profits")
async def zen_node(
    # arbitrage_request: ArbitrageRequest = Depends()
) -> dict:
    with Timer(text="\nTotal elapsed time: {:.1f}"):
        zen_info = await asyncio.gather(
            asyncio.create_task(get_zen_node_payments()),
            asyncio.create_task(query_price(BinanceSymbols.ZENUSDT)),
        )

        pmt = SecureNodePayments(**zen_info[0])
        zen_usdt: CurrencyPair = zen_info[1]

        df: pd.DataFrame = pd.DataFrame([r.dict() for r in pmt.rows])
        df2: pd.DataFrame = df.loc[
            (df["status"] == "review") | (df["status"] == "rollup")
        ].sort_values(by=["enddate"], ascending=False)

        mean_pmt = df2.head(10)["zen"].mean()
        sum_pmt = df2.head(30)["zen"].sum()

        gross_ret_mean = mean_pmt * 30 * zen_usdt.price
        gross_ret_sum = sum_pmt * zen_usdt.price

        cost = 6.00

        net_profit_mean = gross_ret_mean - cost
        net_profit_sum = gross_ret_sum - cost

        return {
            "notes": "Price in USD",
            "monthly_payments": {
                "mean_10d": mean_pmt * 30,
                "rolling_30d": sum_pmt,
            },
            "monthly_gross_return": {
                "mean_10d": gross_ret_mean,
                "rolling_30d": gross_ret_sum,
            },
            "monthly_cost": {"vps_monthly": cost},
            "ZEN": {"price": zen_usdt.price},
            "monthly_profit": {
                "mean_10d": net_profit_mean,
                "rolling_30d": net_profit_sum,
            },
        }


if __name__ == "__main__":
    uvicorn.run(app, port=8111, host="127.0.0.1")
