import os
import json
import asyncio
import logging
from datetime import date
from contextlib import asynccontextmanager

import duckdb
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict

from services.yields_query_service.config import db_path
from services.yields_query_service import queries as q

logger = logging.getLogger()
NATS_SUBJECT = "treasury.yields.ingested"


# ---- response models (JSON key for the rate is "yield") --------------------
class CurvePoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    tenor: str
    tenor_order: int
    yield_: float = Field(serialization_alias="yield")


class Curve(BaseModel):
    trading_date: date
    points: list[CurvePoint]


class CurveComparison(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    requested: str
    resolved_trading_date: date | None
    points: list[CurvePoint]


class CurveResponse(BaseModel):
    base: Curve
    comparison: CurveComparison | None = None


class SpreadPoint(BaseModel):
    trading_date: date
    spread_bps: float
    is_inverted: bool


class SeriesPoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    trading_date: date
    yield_: float = Field(serialization_alias="yield")


# ---- SSE broadcaster: fan one NATS event out to all connected clients ------
class Broadcaster:
    def __init__(self):
        self._clients: set[asyncio.Queue] = set()

    async def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._clients.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._clients.discard(queue)

    async def publish(self, data: dict) -> int:
        for queue in list(self._clients):
            queue.put_nowait(data)
        return len(self._clients)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.broadcaster = Broadcaster()
    app.state.nc = None
    url = os.environ.get("NATS_URL")
    if url:
        try:
            import nats

            nc = await nats.connect(url)

            async def _handler(msg):
                try:
                    await app.state.broadcaster.publish(json.loads(msg.data))
                except Exception as exc:  # a bad message must not kill the sub
                    logger.warning(f"bad {NATS_SUBJECT} message: {exc}")

            await nc.subscribe(NATS_SUBJECT, cb=_handler)
            app.state.nc = nc
            logger.info(f"subscribed to {NATS_SUBJECT} on {url}")
        except Exception as exc:  # serving still works without live NATS
            logger.warning(f"NATS unavailable ({exc}); SSE will emit no live events")
    try:
        yield
    finally:
        if app.state.nc is not None:
            await app.state.nc.close()


def format_sse(event: str, data: dict) -> str:
    """Render one SSE frame (`event:` + `data:` + blank-line terminator)."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


app = FastAPI(title="Yields Query Service", lifespan=lifespan)


def get_broadcaster(request: Request) -> Broadcaster:
    return request.app.state.broadcaster


def get_conn():
    try:
        con = duckdb.connect(db_path(), read_only=True)
    except duckdb.Error as exc:  # warehouse not built yet
        raise HTTPException(status_code=503, detail=f"warehouse unavailable: {exc}")
    try:
        yield con
    finally:
        con.close()


def _resolve_base(con, date_param: str) -> date:
    if date_param in ("", "latest", None):
        latest = q.latest_trading_date(con)
        if latest is None:
            raise HTTPException(status_code=404, detail="no yield curve data")
        return latest
    try:
        return date.fromisoformat(date_param)
    except ValueError:
        raise HTTPException(status_code=422, detail="date must be 'latest' or YYYY-MM-DD")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/yields/curve", response_model=CurveResponse)
def get_curve(
    date_param: str = Query("latest", alias="date"),
    vs: str | None = Query(None, description="Comparison selector: 1M / 1Y / YYYY-MM-DD"),
    con=Depends(get_conn),
):
    base_date = _resolve_base(con, date_param)
    base = Curve(trading_date=base_date, points=q.curve_points(con, base_date))
    comparison = None
    if vs:
        target = q.comparison_target(base_date, vs)
        resolved = q.resolve_available_date(con, target)
        points = q.curve_points(con, resolved) if resolved else []
        comparison = CurveComparison(requested=vs, resolved_trading_date=resolved, points=points)
    return CurveResponse(base=base, comparison=comparison)


@app.get("/yields/spread", response_model=list[SpreadPoint])
def get_spread(window: str = Query("2Y"), con=Depends(get_conn)):
    latest = q.latest_trading_date(con)
    if latest is None:
        return []
    return q.spread_series(con, q.window_start(latest, window))


@app.get("/yields/series", response_model=dict[str, list[SeriesPoint]])
def get_series(
    tenors: str = Query("2Y,10Y", description="Comma-separated Tenor labels"),
    window: str = Query("2Y"),
    con=Depends(get_conn),
):
    latest = q.latest_trading_date(con)
    if latest is None:
        return {}
    start = q.window_start(latest, window)
    wanted = [t.strip() for t in tenors.split(",") if t.strip()]
    return {t: q.tenor_series(con, t, start) for t in wanted}


@app.get("/yields/stream")
async def stream(request: Request, broadcaster: Broadcaster = Depends(get_broadcaster)):
    """SSE: pushes a `yields.ingested` event to the client on each NATS message."""
    queue = await broadcaster.subscribe()
    keepalive = float(os.environ.get("SSE_KEEPALIVE_SECONDS", "15"))

    async def event_gen():
        try:
            yield ": connected\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=keepalive)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"  # keep the connection warm
                    continue
                yield format_sse("yields.ingested", data)
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(event_gen(), media_type="text/event-stream")
