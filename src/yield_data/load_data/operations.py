import csv
import logging
from datetime import datetime, date

import duckdb

from yield_data import RAW_TABLE, DATE_FORMAT
from yield_data.load_data.warehouse import ensure_tables
from yield_data.load_data.quality_checks import perform_quality_checks
from yield_data.load_data.metastore import (
    load_all_last_dates,
    save_last_trading_date,
)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def read_rows_from_csv(csv_file_path: str) -> list[tuple[str, date, float]]:
    """Read the normalized (Tenor, Date, Yield) CSV into typed rows."""
    logger.info(f"Reading file on path: {csv_file_path}")
    rows: list[tuple[str, date, float]] = []
    with open(csv_file_path, newline="") as handle:
        for record in csv.DictReader(handle):
            rows.append(
                (
                    record["Tenor"].strip(),
                    datetime.strptime(record["Date"].strip(), DATE_FORMAT).date(),
                    float(record["Yield"]),
                )
            )
    return rows


def select_incremental(rows, last_dates: dict[str, date]):
    """Keep only rows newer than each Tenor's last loaded Trading Date."""
    selected = []
    for tenor, trading_date, value in rows:
        last = last_dates.get(tenor)
        if last is None or trading_date > last:
            selected.append((tenor, trading_date, value))
    return selected


def load_rows(con: duckdb.DuckDBPyConnection, rows, source_path: str) -> None:
    """Idempotent upsert into the raw table (PK on (Tenor, Trading Date))."""
    con.executemany(
        f"""
        INSERT INTO {RAW_TABLE} (TENOR, TRADING_DATE, YIELD, SOURCE_PATH)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (TENOR, TRADING_DATE)
        DO UPDATE SET YIELD = excluded.YIELD, SOURCE_PATH = excluded.SOURCE_PATH, LOAD_TS = now()
        """,
        [(tenor, td, value, source_path) for tenor, td, value in rows],
    )


def advance_metastore(con: duckdb.DuckDBPyConnection, rows) -> None:
    """Advance each Tenor's last Trading Date to the max just loaded."""
    latest: dict[str, date] = {}
    for tenor, trading_date, _ in rows:
        if tenor not in latest or trading_date > latest[tenor]:
            latest[tenor] = trading_date
    for tenor, trading_date in latest.items():
        save_last_trading_date(con, tenor, trading_date)


def load_csv(con: duckdb.DuckDBPyConnection, csv_file_path: str) -> int:
    """End-to-end load of one normalized CSV. Returns rows written.

    Order: validate the whole batch (write nothing on failure) → ensure tables →
    incremental filter per Tenor → idempotent upsert → advance the metastore.
    """
    rows = read_rows_from_csv(csv_file_path)
    perform_quality_checks(rows)  # raises before any write on a bad batch

    ensure_tables(con)
    new_rows = select_incremental(rows, load_all_last_dates(con))
    if not new_rows:
        logger.info("No new observations to load.")
        return 0

    load_rows(con, new_rows, source_path=csv_file_path)
    advance_metastore(con, new_rows)
    logger.info(f"Loaded {len(new_rows)} new observations from {csv_file_path}.")
    return len(new_rows)
