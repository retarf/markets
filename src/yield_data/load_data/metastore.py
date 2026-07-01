from datetime import date

import duckdb

from yield_data import METASTORE_TABLE


def load_last_trading_date(con: duckdb.DuckDBPyConnection, tenor: str) -> date | None:
    """Last loaded Trading Date for a Tenor, or None if never loaded."""
    row = con.execute(
        f"SELECT LAST_TRADING_DATE FROM {METASTORE_TABLE} WHERE TENOR = ?",
        [tenor],
    ).fetchone()
    return row[0] if row else None


def load_all_last_dates(con: duckdb.DuckDBPyConnection) -> dict[str, date]:
    """The whole metastore as a {Tenor: last Trading Date} map."""
    rows = con.execute(
        f"SELECT TENOR, LAST_TRADING_DATE FROM {METASTORE_TABLE}"
    ).fetchall()
    return {tenor: last_date for tenor, last_date in rows}


def save_last_trading_date(
    con: duckdb.DuckDBPyConnection, tenor: str, last_trading_date: date
) -> None:
    """Upsert the last loaded Trading Date for a Tenor (idempotent)."""
    con.execute(
        f"""
        INSERT INTO {METASTORE_TABLE} (TENOR, LAST_TRADING_DATE)
        VALUES (?, ?)
        ON CONFLICT (TENOR) DO UPDATE SET LAST_TRADING_DATE = excluded.LAST_TRADING_DATE
        """,
        [tenor, last_trading_date],
    )
