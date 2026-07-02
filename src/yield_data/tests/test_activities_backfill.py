import io
import csv

import pytest

from yield_data import RAW_TABLE
from yield_data import activities
from yield_data.fetch_data import operations as fetch_ops
from yield_data.activities import ingest_year_activity
from yield_data.backfill import backfill_years
from yield_data.load_data.warehouse import get_connection


HEADER = [
    "Date", "1 Mo", "1.5 Month", "2 Mo", "3 Mo", "4 Mo", "6 Mo",
    "1 Yr", "2 Yr", "3 Yr", "5 Yr", "7 Yr", "10 Yr", "20 Yr", "30 Yr",
]
VALUES = ["3.70", "3.74", "3.77", "3.87", "3.92", "4.01",
          "3.98", "4.14", "4.15", "4.19", "4.30", "4.44", "4.93", "4.91"]


def fake_curve_for_year(year: str) -> str:
    """One canned Treasury row dated 06/30/<year> (11 tracked Tenors)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(HEADER)
    writer.writerow([f"06/30/{year}"] + VALUES)
    return buffer.getvalue()


@pytest.fixture
def wired(tmp_path, monkeypatch):
    # Stub only the network fetch; land CSVs under a temp datalake.
    monkeypatch.setattr(activities, "fetch_data", lambda year: fake_curve_for_year(year))
    monkeypatch.setattr(fetch_ops, "DATALAKE", str(tmp_path / "datalake"))
    return {"db": str(tmp_path / "wh.duckdb")}


def _count(db_path):
    con = get_connection(db_path)
    try:
        return con.execute(f"SELECT COUNT(*) FROM {RAW_TABLE}").fetchone()[0]
    finally:
        con.close()


def test__ingest_year_activity__lands_and_loads(wired):
    written = ingest_year_activity("2026", "2026-07-01", db_path=wired["db"])

    assert written == 11  # 11 tracked Tenors for the one date
    assert _count(wired["db"]) == 11


def test__backfill_years__accumulates_across_years(wired):
    total = backfill_years(2024, 2026, db_path=wired["db"], capture_date="2026-07-01")

    assert total == 33  # 3 years x 11 Tenors
    assert _count(wired["db"]) == 33


def test__backfill_years__is_resumable_and_idempotent(wired):
    backfill_years(2024, 2026, db_path=wired["db"], capture_date="2026-07-01")

    # Re-running (as a resume would) writes nothing new and creates no duplicates.
    again = backfill_years(2024, 2026, db_path=wired["db"], capture_date="2026-07-01")

    assert again == 0
    assert _count(wired["db"]) == 33
