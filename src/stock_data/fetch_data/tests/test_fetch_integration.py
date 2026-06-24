"""End-to-end fetch -> CSV -> datalake test using a recorded Yahoo payload.

No live network call: `requests.get` is monkeypatched to return a captured
shape of the Yahoo chart response, so the test asserts the full datalake CSV
contract (`Date,Open,High,Low,Close,Volume`, ISO dates, null bars dropped)
deterministically.
"""

import csv

import pytest

from stock_data.fetch_data import operations
from stock_data.fetch_data.operations import (
    fetch_data,
    validate_data,
    build_csv,
    create_dated_directory,
    save_data,
    CSV_HEADER,
)


# Recorded shape of query1.finance.yahoo.com/v8/finance/chart/XTB.WA (trimmed).
# Warsaw is UTC+2 in summer (gmtoffset 7200); timestamps are 00:00 local.
# 2024-07-04 has a null bar (a half/holiday gap) and must be dropped.
RECORDED_PAYLOAD = {
    "chart": {
        "result": [
            {
                "meta": {
                    "currency": "PLN",
                    "symbol": "XTB.WA",
                    "exchangeName": "WSE",
                    "gmtoffset": 7200,
                    "dataGranularity": "1d",
                },
                "timestamp": [1719784800, 1719871200, 1719957600, 1720044000],
                "indicators": {
                    "quote": [
                        {
                            "open": [50.0, 51.0, None, 52.5],
                            "high": [51.2, 51.8, None, 53.0],
                            "low": [49.5, 50.4, None, 52.0],
                            "close": [51.0, 50.9, None, 52.8],
                            "volume": [120000, 98000, None, 110000],
                        }
                    ]
                },
            }
        ],
        "error": None,
    }
}


@pytest.fixture
def yahoo_env(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "DATA_SOURCE_URI",
        "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        "?period1=0&period2=9999999999&interval=1d",
    )

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return RECORDED_PAYLOAD

    monkeypatch.setattr(operations.requests, "get", lambda *a, **k: _Resp())
    # Land the dated datalake directory under tmp_path, not the real datalake.
    monkeypatch.setattr(operations, "DATALAKE", str(tmp_path / "STOCK_DATA"))
    return tmp_path


def test__fetch_to_csv__produces_valid_daily_contract(yahoo_env):
    ticker = "XTB.WA"
    date = "2024-07-04"

    payload = fetch_data(ticker)
    validate_data(ticker, payload)
    data = build_csv(payload)
    dated_directory = create_dated_directory(date)
    save_data(dated_directory, ticker, data)

    written = yahoo_env / "STOCK_DATA" / f"dt={date}" / "XTB.WA.csv"
    assert written.exists()

    rows = list(csv.reader(written.read_text().splitlines()))
    header, body = rows[0], rows[1:]

    # Contract: exact header, ISO dates, the null bar dropped (3 of 4 days kept).
    assert header == CSV_HEADER
    assert len(body) == 3
    assert [r[0] for r in body] == ["2024-07-01", "2024-07-02", "2024-07-04"]
    assert all(len(r) == len(CSV_HEADER) for r in body)
    # No empty fields survived.
    assert all(field != "" for r in body for field in r)
