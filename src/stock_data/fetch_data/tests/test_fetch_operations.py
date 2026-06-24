import pytest

from stock_data.fetch_data import operations
from stock_data.fetch_data.operations import (
    fetch_data,
    validate_data,
    parse_chart_to_rows,
    build_csv,
    save_data,
    CSV_HEADER,
    USER_AGENT,
    ValidationError,
)


def make_payload(gmtoffset=0):
    # 1704153600 == 2024-01-02 00:00:00 UTC, 1704240000 == 2024-01-03 00:00:00 UTC
    return {
        "chart": {
            "error": None,
            "result": [
                {
                    "meta": {"gmtoffset": gmtoffset},
                    "timestamp": [1704153600, 1704240000],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10.0, None],
                                "high": [11.0, 12.0],
                                "low": [9.0, 8.0],
                                "close": [10.5, 11.5],
                                "volume": [1000, 2000],
                            }
                        ]
                    },
                }
            ],
        }
    }


def test__parse_chart_to_rows__drops_incomplete_bars():
    rows = parse_chart_to_rows(make_payload())

    assert rows == [("2024-01-02", 10.0, 11.0, 9.0, 10.5, 1000)]


def test__parse_chart_to_rows__uses_gmtoffset_for_local_date():
    payload = make_payload(gmtoffset=7200)
    # 22:00 UTC on 2024-01-01; +7200s offset rolls the local trading date to 2024-01-02
    payload["chart"]["result"][0]["timestamp"] = [1704153600 - 7200]
    payload["chart"]["result"][0]["indicators"]["quote"][0] = {
        "open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0], "volume": [1],
    }

    rows = parse_chart_to_rows(payload)

    assert rows[0][0] == "2024-01-02"


def test__build_csv__has_header_and_only_valid_rows():
    text = build_csv(make_payload()).decode("utf-8").splitlines()

    assert text[0] == ",".join(CSV_HEADER)
    assert text[1].startswith("2024-01-02,")
    assert len(text) == 2  # header + single complete bar


@pytest.mark.parametrize(
    "payload",
    [
        {"chart": {"error": {"code": "Not Found"}, "result": None}},
        {"chart": {"error": None, "result": []}},
        {"chart": {"error": None, "result": [{"meta": {}}]}},
    ],
)
def test__validate_data__raises_on_no_data(payload):
    with pytest.raises(ValidationError):
        validate_data("nope.wa", payload)


def test__validate_data__passes_for_valid_payload():
    validate_data("xtb.wa", make_payload())


def test__validate_data__error_message_names_ticker():
    payload = {"chart": {"error": {"code": "Not Found"}, "result": None}}

    with pytest.raises(ValidationError, match="XTB.WA"):
        validate_data("xtb.wa", payload)


def test__parse_chart_to_rows__defaults_gmtoffset_to_zero():
    payload = make_payload()
    del payload["chart"]["result"][0]["meta"]["gmtoffset"]

    rows = parse_chart_to_rows(payload)

    assert rows[0][0] == "2024-01-02"


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.raised = False

    def raise_for_status(self):
        self.raised = True

    def json(self):
        return self._payload


def test__fetch_data__formats_url_and_sends_simple_user_agent(monkeypatch):
    monkeypatch.setenv(
        "DATA_SOURCE_URI", "https://example.test/chart/{ticker}?interval=1d"
    )
    captured = {}

    def fake_get(url, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _FakeResponse(make_payload())

    monkeypatch.setattr(operations.requests, "get", fake_get)

    payload = fetch_data("XTB.WA")

    assert captured["url"] == "https://example.test/chart/XTB.WA?interval=1d"
    assert captured["headers"] == {"User-Agent": USER_AGENT}
    assert captured["timeout"] == 30
    assert payload == make_payload()


def test__save_data__writes_verbatim_dotted_filename(tmp_path):
    save_data(tmp_path, "XTB.WA", b"Date,Open\n2024-01-02,10.0\n")

    written = tmp_path / "XTB.WA.csv"
    assert written.exists()
    assert written.read_bytes() == b"Date,Open\n2024-01-02,10.0\n"
