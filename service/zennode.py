import datetime
from typing import List, Optional

import httpx
from codetiming import Timer
from pydantic.main import BaseModel


class SecureNodeUserData(BaseModel):
    total: int


class SecureNodeRow(BaseModel):
    id: int
    status: str
    startdate: datetime.datetime
    enddate: datetime.datetime
    pmid: int
    uptime: Optional[float]
    zen: float
    rollupid: Optional[int]
    paidat: Optional[datetime.datetime]
    txid: Optional[str]


class SecureNodePayments(BaseModel):
    total: int
    page: int
    records: int
    rows: List[SecureNodeRow]
    userdata: SecureNodeUserData


async def get_zen_node_payments():
    timer = Timer(text=f"Task ZEN PAYMENTS elapsed time: {{:.1f}}")

    timer.start()
    url = "https://securenodes2.eu.zensystem.io/grid/348943/pmts"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()

        timer.stop()
        return resp.json()
