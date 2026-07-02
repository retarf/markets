def test__health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test__curve_latest__maturity_ordered_with_yield_key(client):
    r = client.get("/yields/curve")
    assert r.status_code == 200
    body = r.json()
    assert body["base"]["trading_date"] == "2026-06-30"
    orders = [p["tenor_order"] for p in body["base"]["points"]]
    assert orders == sorted(orders)  # maturity order
    assert body["base"]["points"][0]["tenor"] == "3M"
    assert "yield" in body["base"]["points"][0]  # JSON key is "yield", not "yield_"
    assert body["comparison"] is None


def test__curve_by_date(client):
    r = client.get("/yields/curve", params={"date": "2025-06-30"})
    assert r.json()["base"]["trading_date"] == "2025-06-30"


def test__curve_gap__missing_tenor_absent_not_zero(client):
    # 2026-06-29 has no 3M print -> that point is absent, not a 0.
    pts = client.get("/yields/curve", params={"date": "2026-06-29"}).json()["base"]["points"]
    tenors = [p["tenor"] for p in pts]
    assert "3M" not in tenors
    assert tenors == ["2Y", "10Y"]


def test__curve_compare_1y__exact_date_present(client):
    body = client.get("/yields/curve", params={"vs": "1Y"}).json()
    comp = body["comparison"]
    assert comp["requested"] == "1Y"
    assert comp["resolved_trading_date"] == "2025-06-30"  # exactly one year back exists
    assert comp["points"]


def test__curve_compare_1m__resolves_nearest_prior(client):
    # latest 2026-06-30 minus 1M = 2026-05-30 (no data) -> nearest prior 2026-05-29
    comp = client.get("/yields/curve", params={"vs": "1M"}).json()["comparison"]
    assert comp["resolved_trading_date"] == "2026-05-29"


def test__spread_window_2y__includes_inverted(client):
    rows = client.get("/yields/spread", params={"window": "2Y"}).json()
    dates = [r["trading_date"] for r in rows]
    assert "2025-06-30" in dates
    inverted = next(r for r in rows if r["trading_date"] == "2025-06-30")
    assert inverted["is_inverted"] is True and inverted["spread_bps"] == -70


def test__spread_window_6m__filters_out_old(client):
    rows = client.get("/yields/spread", params={"window": "6M"}).json()
    dates = [r["trading_date"] for r in rows]
    assert "2025-06-30" not in dates  # older than 6 months
    assert "2026-06-30" in dates


def test__series__two_legs_with_yield_key(client):
    body = client.get("/yields/series", params={"tenors": "2Y,10Y", "window": "max"}).json()
    assert set(body) == {"2Y", "10Y"}
    assert body["10Y"][-1]["trading_date"] == "2026-06-30"
    assert "yield" in body["2Y"][0]


def test__curve_warehouse_missing__returns_503(client, monkeypatch):
    monkeypatch.setenv("YIELD_WAREHOUSE_DB", "/nonexistent/nope.duckdb")
    assert client.get("/yields/curve").status_code == 503
