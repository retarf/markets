"""Plain-Python historical backfill over a range of years.

This is the *logic* the Temporal backfill workflow wraps for durability. It is
resumable and idempotent by construction: the per-Tenor metastore incremental
filter and the raw table's `(Tenor, Trading Date)` primary key mean re-running an
already-loaded year loads zero rows, so an interrupted backfill simply resumes by
being re-run. Kept engine-free so it can run and be tested with no Temporal.
"""

import time
import logging
from datetime import date

from yield_data import DATE_FORMAT
from yield_data.activities import ingest_year_activity


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def backfill_years(
    start_year: int,
    end_year: int,
    db_path: str | None = None,
    capture_date: str | None = None,
    pace_seconds: float = 0.0,
) -> int:
    """Ingest every year in ``[start_year, end_year]``. Returns total rows written.

    ``pace_seconds`` throttles requests to be polite to the Treasury endpoint.
    """
    capture = capture_date or date.today().strftime(DATE_FORMAT)
    total = 0
    for year in range(start_year, end_year + 1):
        written = ingest_year_activity(str(year), capture, db_path)
        logger.info(f"Backfill year {year}: {written} rows")
        total += written
        if pace_seconds and year != end_year:
            time.sleep(pace_seconds)
    return total
