def test__health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test__proxy_forwards_to_query_service(client):
    r = client.get("/api/yields/curve", params={"date": "latest"})
    assert r.status_code == 200
    body = r.json()
    assert body["base"]["trading_date"] == "2026-06-30"
    assert body["base"]["points"][0]["tenor"] == "3M"


def test__proxy_forwards_query_params(client):
    # window is honoured end-to-end through the gateway
    r = client.get("/api/yields/spread", params={"window": "max"})
    assert r.status_code == 200
    assert r.json()[0]["spread_bps"] == 30


def test__proxy_passes_through_upstream_error_status(client):
    # bad date -> query service 422 -> gateway 422
    assert client.get("/api/yields/curve", params={"date": "not-a-date"}).status_code == 422


def test__cors_allows_frontend_origin(client):
    r = client.get("/api/yields/curve", headers={"origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
