from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.chembl import ChEMBLProvider, UpstreamError
from backend.integrations import CompoundProvider
from backend import oncocompute


@asynccontextmanager
async def lifespan(app: FastAPI):
    with httpx.Client(timeout=20, follow_redirects=False) as client:
        app.state.provider = ChEMBLProvider(client)
        yield


app = FastAPI(title="OncoResearch AI", version="0.1.0", lifespan=lifespan)


def get_provider(request: Request) -> CompoundProvider:
    return request.app.state.provider


@app.get("/health")
def health():
    return {"status": "ok", "chembl": "configured; not probed", "pharmalab": "adapted scripts", "oncocompute": oncocompute.status()}


class MeanRequest(BaseModel):
    values: list[Annotated[float, Field(strict=True, allow_inf_nan=False, ge=-1e100, le=1e100)]] = Field(min_length=1, max_length=10000)
    unit: str = Field(min_length=1, max_length=60, pattern=r"\S")


@app.post("/oncocompute/mean")
def mean(request: MeanRequest):
    try:
        return oncocompute.calculate_mean(request.values, request.unit.strip())
    except oncocompute.NativeUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@app.get("/compounds/search")
def search(
    q: Annotated[str, Query(min_length=1, max_length=120)],
    provider: Annotated[CompoundProvider, Depends(get_provider)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
):
    query = q.strip()
    if not query:
        raise HTTPException(422, "Enter a compound name.")
    try:
        return provider.search(query, limit)
    except UpstreamError as exc:
        raise HTTPException(502, str(exc)) from exc
