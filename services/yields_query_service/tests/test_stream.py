import asyncio

from starlette.responses import StreamingResponse

from services.yields_query_service.app import Broadcaster, format_sse, stream


def test__broadcaster__fans_out_to_all_subscribers():
    async def scenario():
        b = Broadcaster()
        q1, q2 = await b.subscribe(), await b.subscribe()
        n = await b.publish({"trading_date": "2026-06-30", "tenors": ["2Y", "10Y"]})
        return n, await q1.get(), await q2.get()

    n, a, b = asyncio.run(scenario())
    assert n == 2
    assert a["trading_date"] == "2026-06-30" and b == a


def test__broadcaster__unsubscribe_stops_delivery():
    async def scenario():
        b = Broadcaster()
        q = await b.subscribe()
        b.unsubscribe(q)
        return await b.publish({"x": 1})

    assert asyncio.run(scenario()) == 0


def test__format_sse__frames_event_and_data():
    frame = format_sse("yields.ingested", {"trading_date": "2026-06-30"})
    assert frame == 'event: yields.ingested\ndata: {"trading_date": "2026-06-30"}\n\n'


class _FakeRequest:
    async def is_disconnected(self):
        return True


def test__stream_endpoint__returns_event_stream_response():
    # Call the handler directly; do NOT drain the (infinite) body.
    resp = asyncio.run(stream(_FakeRequest(), Broadcaster()))
    assert isinstance(resp, StreamingResponse)
    assert resp.media_type == "text/event-stream"
