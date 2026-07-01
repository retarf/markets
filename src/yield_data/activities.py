"""Reusable ingestion activities shared by the Airflow daily pull and the
Temporal backfill. These are plain functions (no orchestrator imports) so the
same code path runs under either engine and can be unit-tested directly.
"""

import logging

from yield_data.fetch_data.operations import (
    fetch_data,
    validate_data,
    build_csv,
    create_dated_directory,
    save_data,
)
from yield_data.load_data.warehouse import get_connection
from yield_data.load_data.operations import load_csv


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def fetch_year_activity(year: str, capture_date: str) -> str:
    """Fetch a year's Treasury curve, validate, normalize, and land the CSV.

    Returns the path of the normalized CSV in the dated datalake partition.
    """
    payload = fetch_data(year)
    validate_data(year, payload)
    data = build_csv(payload)
    directory = create_dated_directory(capture_date)
    path = save_data(directory, data)
    logger.info(f"Landed Treasury year {year} under dt={capture_date}: {path}")
    return str(path)


def load_activity(csv_path: str, db_path: str | None = None) -> int:
    """Load a landed normalized CSV into the DuckDB warehouse. Returns rows written."""
    con = get_connection(db_path)
    try:
        return load_csv(con, csv_path)
    finally:
        con.close()


def ingest_year_activity(year: str, capture_date: str, db_path: str | None = None) -> int:
    """Fetch+land then load one year. Rows written (idempotent/incremental)."""
    path = fetch_year_activity(year, capture_date)
    return load_activity(path, db_path)
