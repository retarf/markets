import os

import duckdb

from yield_data import (
    WAREHOUSE_DB,
    DEFAULT_WAREHOUSE_DB,
    RAW_TABLE,
    METASTORE_TABLE,
)


def get_connection(db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    """Open (and lazily create) the local DuckDB warehouse.

    Pass an explicit path (e.g. ``":memory:"`` in tests) or fall back to the
    ``YIELD_WAREHOUSE_DB`` env var / the datalake default.
    """
    path = db_path or os.environ.get(WAREHOUSE_DB) or DEFAULT_WAREHOUSE_DB
    return duckdb.connect(path)


def ensure_tables(con: duckdb.DuckDBPyConnection) -> None:
    """Create the raw yields table and the per-Tenor metastore if absent.

    The raw table's primary key ``(TENOR, TRADING_DATE)`` makes loads idempotent.
    """
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {RAW_TABLE} (
            TENOR         VARCHAR   NOT NULL,
            TRADING_DATE  DATE      NOT NULL,
            YIELD         DOUBLE    NOT NULL,
            SOURCE_PATH   VARCHAR,
            LOAD_TS       TIMESTAMP DEFAULT now(),
            PRIMARY KEY (TENOR, TRADING_DATE)
        )
        """
    )
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {METASTORE_TABLE} (
            TENOR              VARCHAR NOT NULL PRIMARY KEY,
            LAST_TRADING_DATE  DATE    NOT NULL
        )
        """
    )
