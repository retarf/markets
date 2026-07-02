import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask


def query_service_url() -> str:
    return os.environ.get("QUERY_SERVICE_URL", "http://yields-query-service:8000")


def frontend_origin() -> str:
    return os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")


# Hop-by-hop headers that must not be forwarded verbatim.
_DROP_HEADERS = {"content-length", "content-encoding", "transfer-encoding", "connection"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=None)
    try:
        yield
    finally:
        await app.state.http.aclose()


app = FastAPI(title="Yields API Gateway", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin()],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/yields/{path:path}")
async def proxy(path: str, request: Request):
    """Forward /api/yields/* to the query service, streaming the response.

    Streaming makes SSE (`/api/yields/stream`) pass through unbuffered.
    """
    client: httpx.AsyncClient = request.app.state.http
    upstream = client.build_request(
        "GET",
        f"{query_service_url()}/yields/{path}",
        params=request.query_params,
    )
    resp = await client.send(upstream, stream=True)
    headers = {k: v for k, v in resp.headers.items() if k.lower() not in _DROP_HEADERS}
    return StreamingResponse(
        resp.aiter_raw(),
        status_code=resp.status_code,
        headers=headers,
        media_type=resp.headers.get("content-type"),
        background=BackgroundTask(resp.aclose),
    )
