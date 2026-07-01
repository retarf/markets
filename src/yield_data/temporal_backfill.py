"""Temporal durable backfill for the YIELD_DATA domain.

This is the durable-execution *shell* around the plain, unit-tested logic in
``yield_data.activities`` / ``yield_data.backfill``. Each year is a retryable
Temporal activity; the workflow loops years, so an interrupted backfill resumes
from Temporal's event history without re-loading already-loaded rows (loads are
idempotent by the per-Tenor metastore + the raw table's primary key).

Requires (verified in dev-verify, not in the local pytest gate):
  - `pip install temporalio`
  - a running Temporal server (see docker-compose `temporal` service)

Run a worker:   python -m yield_data.temporal_backfill
Start a backfill (from a client):
    asyncio.run(start_backfill(2015, 2024, "2026-07-01"))
"""

import asyncio
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker


TASK_QUEUE = "yield-backfill"


@activity.defn
def ingest_year(year: str, capture_date: str, db_path: str | None) -> int:
    # Reuse the exact same activity the Airflow daily pull uses.
    from yield_data.activities import ingest_year_activity

    return ingest_year_activity(year, capture_date, db_path)


@workflow.defn
class TreasuryBackfillWorkflow:
    @workflow.run
    async def run(
        self,
        start_year: int,
        end_year: int,
        capture_date: str,
        db_path: str | None = None,
    ) -> int:
        total = 0
        for year in range(start_year, end_year + 1):
            total += await workflow.execute_activity(
                ingest_year,
                args=[str(year), capture_date, db_path],
                start_to_close_timeout=timedelta(minutes=10),
                # A short heartbeat timeout bounds crash-resume latency: if the
                # worker dies mid-year, Temporal retries the (idempotent) activity
                # on another worker within ~30s instead of waiting out
                # start_to_close_timeout. The activity is fast enough not to need
                # explicit heartbeats.
                heartbeat_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=5),
            )
        return total


async def run_worker(address: str = "localhost:7233") -> None:
    client = await Client.connect(address)
    with ThreadPoolExecutor(max_workers=4) as executor:
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[TreasuryBackfillWorkflow],
            activities=[ingest_year],
            activity_executor=executor,
        )
        await worker.run()


async def start_backfill(
    start_year: int,
    end_year: int,
    capture_date: str,
    db_path: str | None = None,
    address: str = "localhost:7233",
) -> int:
    client = await Client.connect(address)
    return await client.execute_workflow(
        TreasuryBackfillWorkflow.run,
        args=[start_year, end_year, capture_date, db_path],
        id=f"treasury-backfill-{start_year}-{end_year}",
        task_queue=TASK_QUEUE,
    )


if __name__ == "__main__":
    asyncio.run(run_worker())
