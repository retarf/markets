from datetime import date

import duckdb
import pytest
from fastapi.testclient import TestClient


# tenor_order: 3M=1, 2Y=4, 10Y=8 (matches fct_yield_curve maturity ranks)
CURVE_ROWS = [
    # 2025-06-30 — inverted (2Y > 10Y)
    (date(2025, 6, 30), "3M", 1, 4.30),
    (date(2025, 6, 30), "2Y", 4, 4.90),
    (date(2025, 6, 30), "10Y", 8, 4.20),
    # 2026-05-29 — normal
    (date(2026, 5, 29), "2Y", 4, 4.10),
    (date(2026, 5, 29), "10Y", 8, 4.38),
    # 2026-06-29 — normal, but 3M is a GAP (absent, not zero)
    (date(2026, 6, 29), "2Y", 4, 4.10),
    (date(2026, 6, 29), "10Y", 8, 4.38),
    # 2026-06-30 — latest, full
    (date(2026, 6, 30), "3M", 1, 3.87),
    (date(2026, 6, 30), "2Y", 4, 4.14),
    (date(2026, 6, 30), "10Y", 8, 4.44),
]
SPREAD_ROWS = [
    (date(2025, 6, 30), -70.0, True),
    (date(2026, 5, 29), 28.0, False),
    (date(2026, 6, 29), 28.0, False),
    (date(2026, 6, 30), 30.0, False),
]


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = tmp_path / "wh.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create table fct_yield_curve(trading_date DATE, tenor VARCHAR, tenor_order INTEGER, yield DOUBLE)")
    con.execute("create table fct_2s10s_spread(trading_date DATE, spread_bps DOUBLE, is_inverted BOOLEAN)")
    con.executemany("insert into fct_yield_curve values (?,?,?,?)", CURVE_ROWS)
    con.executemany("insert into fct_2s10s_spread values (?,?,?)", SPREAD_ROWS)
    con.close()

    monkeypatch.setenv("YIELD_WAREHOUSE_DB", str(db))
    monkeypatch.delenv("NATS_URL", raising=False)  # no live NATS in unit tests
    monkeypatch.setenv("SSE_KEEPALIVE_SECONDS", "0.2")  # keep the stream test snappy
    from services.yields_query_service.app import app

    # `with` runs the lifespan (initialises the SSE broadcaster; skips NATS).
    with TestClient(app) as test_client:
        yield test_client
