import os
import io
import csv
import pathlib
import datetime

import requests
import logging

from yield_data import (
    DATALAKE,
    PROVIDER_DATE_FORMAT,
    DATE_FORMAT,
    TENOR_TO_TREASURY_COLUMN,
    TRACKED_TENORS,
)


# The Treasury CSV endpoint answers a plain GET; a simple client User-Agent is
# used for parity with the equity fetch (no cookie/crumb, no key required).
USER_AGENT = "Mozilla/5.0"

CSV_HEADER = ["Tenor", "Date", "Yield"]

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ValidationError(ValueError):
    pass


def fetch_data(year):
    data_url = os.environ.get("TREASURY_YIELDS_URI")
    response = requests.get(
        data_url.format(year=year),
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )  # requests.exceptions.Timeout or ReadTimeout
    response.raise_for_status()  # HTTPError
    return response.text


def validate_data(year, payload):
    reader = csv.reader(io.StringIO(payload))
    header = next(reader, None)
    if not header or header[0].strip().lower() != "date":
        raise ValidationError(
            f"No Treasury yield curve data found for year {year}"
        )
    tracked_columns = set(TENOR_TO_TREASURY_COLUMN.values())
    present = {col.strip() for col in header}
    missing = tracked_columns - present
    if missing:
        raise ValidationError(
            f"Treasury response for year {year} is missing expected Tenor columns: {sorted(missing)}"
        )


def parse_curve_to_rows(payload):
    """Normalise the wide Treasury curve CSV into (Tenor, ISO date, Yield) rows.

    Empty cells are gaps and are dropped — never zero-filled or interpolated.
    Only the tracked Tenor columns are kept, in maturity order per Trading Date.
    """
    reader = csv.DictReader(io.StringIO(payload))

    rows = []
    for record in reader:
        raw_date = (record.get("Date") or "").strip()
        if not raw_date:
            continue
        trading_date = datetime.datetime.strptime(
            raw_date, PROVIDER_DATE_FORMAT
        ).strftime(DATE_FORMAT)

        for tenor in TRACKED_TENORS:
            column = TENOR_TO_TREASURY_COLUMN[tenor]
            value = (record.get(column) or "").strip()
            if value == "":
                continue  # gap — no print for this Tenor on this Trading Date
            rows.append((tenor, trading_date, float(value)))

    return rows


def build_csv(payload):
    rows = parse_curve_to_rows(payload)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def create_dated_directory(date_string: str) -> pathlib.Path:
    custom_path = f"{DATALAKE}/dt={date_string}"
    path = pathlib.Path(custom_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_data(dated_directory, data):
    path = pathlib.Path(dated_directory / "treasury_yields.csv")
    path.write_bytes(data)
    logger.info(f"Data has been wrote to {str(path)}")
    return path
