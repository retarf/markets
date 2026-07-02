"""NATS event publishing for the YIELD_DATA domain.

The ingestion side emits `treasury.yields.ingested {trading_date, tenors}` after a
load advances the warehouse. Publishing is **optional**: if `NATS_URL` is unset
(or `nats-py` isn't installed), this is a no-op — so the data pipeline still runs
fully offline without the serving tier.
"""

import os
import json
import asyncio
import logging

SUBJECT = "treasury.yields.ingested"

logger = logging.getLogger()


async def _publish_async(url: str, payload: bytes) -> None:
    import nats  # lazy: only needed when actually publishing

    nc = await nats.connect(url)
    try:
        await nc.publish(SUBJECT, payload)
        await nc.flush()
    finally:
        await nc.close()


def emit_yields_ingested(trading_date, tenors) -> bool:
    """Publish the ingestion event. Returns True if published, False if skipped.

    Skips silently when `NATS_URL` is not configured (offline data-pipeline runs).
    """
    url = os.environ.get("NATS_URL")
    if not url:
        return False
    payload = json.dumps(
        {"trading_date": str(trading_date), "tenors": sorted(tenors)}
    ).encode()
    try:
        asyncio.run(_publish_async(url, payload))
        logger.info(f"Published {SUBJECT} for {trading_date} ({len(tenors)} tenors)")
        return True
    except Exception as exc:  # never let event publishing break ingestion
        logger.warning(f"Failed to publish {SUBJECT}: {exc}")
        return False
