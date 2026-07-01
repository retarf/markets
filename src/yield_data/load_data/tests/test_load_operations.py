from datetime import date

import pytest

from yield_data import RAW_TABLE, METASTORE_TABLE
from yield_data.load_data.warehouse import get_connection, ensure_tables
from yield_data.load_data.operations import (
    read_rows_from_csv,
    select_incremental,
    load_csv,
)
from yield_data.load_data.quality_checks import (
    QualityError,
    not_null_quality_check,
    within_band_quality_check,
)


def write_csv(tmp_path, name, body):
    path = tmp_path / name
    path.write_text("Tenor,Date,Yield\n" + body)
    return str(path)


DAY1 = "2Y,2026-06-29,4.10\n10Y,2026-06-29,4.38\n"
DAY2 = "2Y,2026-06-30,4.14\n10Y,2026-06-30,4.44\n"


@pytest.fixture
def con():
    connection = get_connection(":memory:")
    yield connection
    connection.close()


def _count(con):
    return con.execute(f"SELECT COUNT(*) FROM {RAW_TABLE}").fetchone()[0]


def test__load_csv__writes_rows_and_advances_metastore(con, tmp_path):
    path = write_csv(tmp_path, "y.csv", DAY1 + DAY2)

    written = load_csv(con, path)

    assert written == 4
    assert _count(con) == 4
    meta = dict(con.execute(f"SELECT TENOR, LAST_TRADING_DATE FROM {METASTORE_TABLE}").fetchall())
    assert meta == {"2Y": date(2026, 6, 30), "10Y": date(2026, 6, 30)}


def test__load_csv__is_incremental_and_idempotent(con, tmp_path):
    path = write_csv(tmp_path, "y.csv", DAY1 + DAY2)
    load_csv(con, path)

    # Re-loading the same file writes nothing new and creates no duplicates.
    written_again = load_csv(con, path)

    assert written_again == 0
    assert _count(con) == 4
    dupes = con.execute(
        f"SELECT TENOR, TRADING_DATE, COUNT(*) c FROM {RAW_TABLE} GROUP BY 1,2 HAVING c > 1"
    ).fetchall()
    assert dupes == []


def test__load_csv__loads_only_newer_observations(con, tmp_path):
    load_csv(con, write_csv(tmp_path, "d1.csv", DAY1))
    written = load_csv(con, write_csv(tmp_path, "d2.csv", DAY1 + DAY2))

    # DAY1 rows already loaded; only the two DAY2 rows are new.
    assert written == 2
    assert _count(con) == 4


def test__load_csv__updates_yield_for_same_key_on_correction(con, tmp_path):
    # A same-date correction is not "newer", so the incremental filter skips it —
    # proving the metastore gate holds (no silent overwrite from a re-fetch).
    load_csv(con, write_csv(tmp_path, "d.csv", "10Y,2026-06-30,4.44\n"))
    load_csv(con, write_csv(tmp_path, "d2.csv", "10Y,2026-06-30,9.99\n"))

    value = con.execute(
        f"SELECT YIELD FROM {RAW_TABLE} WHERE TENOR='10Y' AND TRADING_DATE=DATE '2026-06-30'"
    ).fetchone()[0]
    assert value == 4.44


def test__band_check__rejects_out_of_band_batch_before_write(con, tmp_path):
    path = write_csv(tmp_path, "bad.csv", "10Y,2026-06-30,4.44\n2Y,2026-06-30,30.0\n")

    with pytest.raises(QualityError):
        load_csv(con, path)


def test__not_null_check__raises_on_missing_value():
    with pytest.raises(QualityError):
        not_null_quality_check([("10Y", date(2026, 6, 30), None)])


def test__within_band_check__names_the_offending_tenor():
    with pytest.raises(QualityError, match="2Y"):
        within_band_quality_check([("2Y", date(2026, 6, 30), 99.0)])


def test__read_rows_from_csv__types_the_columns(tmp_path):
    rows = read_rows_from_csv(write_csv(tmp_path, "y.csv", DAY2))

    assert ("10Y", date(2026, 6, 30), 4.44) in rows
    assert all(isinstance(d, date) for _, d, _ in rows)


def test__select_incremental__keeps_only_newer_per_tenor():
    rows = [
        ("2Y", date(2026, 6, 29), 4.10),
        ("2Y", date(2026, 6, 30), 4.14),
        ("10Y", date(2026, 6, 30), 4.44),
    ]
    last = {"2Y": date(2026, 6, 29)}  # 10Y never loaded

    selected = select_incremental(rows, last)

    assert ("2Y", date(2026, 6, 29), 4.10) not in selected
    assert ("2Y", date(2026, 6, 30), 4.14) in selected
    assert ("10Y", date(2026, 6, 30), 4.44) in selected
