from datetime import date

import duckdb
import httpx
import pytest
from fastapi.testclient import TestClient


def _make_warehouse(path):
    con = duckdb.connect(str(path))
    con.execute("create table fct_yield_curve(trading_date DATE, tenor VARCHAR, tenor_order INTEGER, yield DOUBLE)")
    con.execute("create table fct_2s10s_spread(trading_date DATE, spread_bps DOUBLE, is_inverted BOOLEAN)")
    con.executemany("insert into fct_yield_curve values (?,?,?,?)", [
        (date(2026, 6, 30), "3M", 1, 3.87),
        (date(2026, 6, 30), "2Y", 4, 4.14),
        (date(2026, 6, 30), "10Y", 8, 4.44),
    ])
    con.executemany("insert into fct_2s10s_spread values (?,?,?)", [
        (date(2026, 6, 30), 30.0, False),
    ])
    con.close()


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = tmp_path / "wh.duckdb"
    _make_warehouse(db)
    monkeypatch.setenv("YIELD_WAREHOUSE_DB", str(db))
    monkeypatch.setenv("QUERY_SERVICE_URL", "http://query")
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://localhost:5173")
    monkeypatch.delenv("NATS_URL", raising=False)

    from services.yields_query_service.app import app as query_app
    from services.api_gateway.app import app as gw_app

    with TestClient(gw_app) as test_client:
        # Gateway talks to the REAL query app in-process (proves the proxy path).
        test_client.app.state.http = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=query_app), base_url="http://query"
        )
        yield test_client
