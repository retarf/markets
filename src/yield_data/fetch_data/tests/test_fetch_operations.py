import io
import csv

import pytest

from yield_data.fetch_data import operations
from yield_data.fetch_data.operations import (
    fetch_data,
    validate_data,
    parse_curve_to_rows,
    build_csv,
    save_data,
    CSV_HEADER,
    USER_AGENT,
    ValidationError,
)


# The real Treasury CSV header, including columns we do NOT track
# ("1.5 Month", "2 Mo", "4 Mo") to prove they are ignored.
HEADER = [
    "Date", "1 Mo", "1.5 Month", "2 Mo", "3 Mo", "4 Mo", "6 Mo",
    "1 Yr", "2 Yr", "3 Yr", "5 Yr", "7 Yr", "10 Yr", "20 Yr", "30 Yr",
]


def make_payload(rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(HEADER)
    writer.writerows(rows)
    return buffer.getvalue()


# 06/30/2026 fully populated; 06/29/2026 with a gap in "2 Yr".
FULL_ROW = [
    "06/30/2026", "3.70", "3.74", "3.77", "3.87", "3.92", "4.01",
    "3.98", "4.14", "4.15", "4.19", "4.30", "4.44", "4.93", "4.91",
]
GAP_ROW = [
    "06/29/2026", "3.71", "3.71", "3.76", "3.87", "3.92", "4.00",
    "3.97", "", "4.10", "4.14", "4.24", "4.38", "4.86", "4.86",
]


def test__parse_curve_to_rows__normalises_wide_row_to_tracked_tenors():
    rows = parse_curve_to_rows(make_payload([FULL_ROW]))

    # 11 tracked Tenors for the single Trading Date; untracked columns ignored.
    assert len(rows) == 11
    assert ("2Y", "2026-06-30", 4.14) in rows
    assert ("10Y", "2026-06-30", 4.44) in rows
    tenors = {tenor for tenor, _, _ in rows}
    assert tenors == {"1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"}


def test__parse_curve_to_rows__converts_us_date_to_iso():
    rows = parse_curve_to_rows(make_payload([FULL_ROW]))

    assert all(date == "2026-06-30" for _, date, _ in rows)


def test__parse_curve_to_rows__drops_empty_cells_as_gaps():
    rows = parse_curve_to_rows(make_payload([GAP_ROW]))

    # 2Y is blank for this date -> absent (not zero, not interpolated).
    assert not any(tenor == "2Y" and date == "2026-06-29" for tenor, date, _ in rows)
    # A populated Tenor on the same date is still present.
    assert ("10Y", "2026-06-29", 4.38) in rows
    assert len(rows) == 10


def test__parse_curve_to_rows__skips_rows_without_a_date():
    empty_date_row = [""] + ["1.00"] * (len(HEADER) - 1)
    rows = parse_curve_to_rows(make_payload([empty_date_row, FULL_ROW]))

    assert {date for _, date, _ in rows} == {"2026-06-30"}


def test__build_csv__has_header_and_normalised_rows():
    text = build_csv(make_payload([FULL_ROW])).decode("utf-8").splitlines()

    assert text[0] == ",".join(CSV_HEADER)
    assert len(text) == 12  # header + 11 tracked Tenors
    assert "2Y,2026-06-30,4.14" in text


@pytest.mark.parametrize(
    "payload",
    [
        "",
        "not,a,yield,curve\n1,2,3,4\n",
    ],
)
def test__validate_data__raises_on_no_data(payload):
    with pytest.raises(ValidationError):
        validate_data("2026", payload)


def test__validate_data__raises_when_tracked_tenor_column_missing():
    header_without_10y = [c for c in HEADER if c != "10 Yr"]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header_without_10y)
    payload = buffer.getvalue()

    with pytest.raises(ValidationError, match="10 Yr"):
        validate_data("2026", payload)


def test__validate_data__passes_for_valid_payload():
    validate_data("2026", make_payload([FULL_ROW]))


def test__validate_data__error_message_names_year():
    with pytest.raises(ValidationError, match="2026"):
        validate_data("2026", "")


class _FakeResponse:
    def __init__(self, text):
        self._text = text
        self.raised = False

    def raise_for_status(self):
        self.raised = True

    @property
    def text(self):
        return self._text


def test__fetch_data__formats_url_and_sends_simple_user_agent(monkeypatch):
    monkeypatch.setenv(
        "TREASURY_YIELDS_URI", "https://example.test/rates.csv/{year}/all?year={year}"
    )
    captured = {}

    def fake_get(url, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _FakeResponse(make_payload([FULL_ROW]))

    monkeypatch.setattr(operations.requests, "get", fake_get)

    payload = fetch_data("2026")

    assert captured["url"] == "https://example.test/rates.csv/2026/all?year=2026"
    assert captured["headers"] == {"User-Agent": USER_AGENT}
    assert captured["timeout"] == 30
    assert payload == make_payload([FULL_ROW])


def test__save_data__writes_normalised_csv(tmp_path):
    save_data(tmp_path, b"Tenor,Date,Yield\n10Y,2026-06-30,4.44\n")

    written = tmp_path / "treasury_yields.csv"
    assert written.exists()
