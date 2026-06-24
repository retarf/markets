import os
import io
import csv
import pathlib
import datetime

import requests
import logging

from stock_data import DATALAKE


# Yahoo's chart endpoint needs a User-Agent (the default python-requests one is
# rejected), but a full desktop-browser UA gets a persistent HTTP 429 — the API
# treats it as a browser scraping the API. A simple client UA is accepted. No
# cookie/crumb is required.
USER_AGENT = "Mozilla/5.0"

CSV_HEADER = ["Date", "Open", "High", "Low", "Close", "Volume"]

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ValidationError(ValueError):
    pass


def fetch_data(ticker):
    data_url = os.environ.get("DATA_SOURCE_URI")
    response = requests.get(
        data_url.format(ticker=ticker),
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )  # requests.exceptions.Timeout or ReadTimeout
    response.raise_for_status()  # HTTPError
    return response.json()


def validate_data(ticker, payload):
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise ValidationError(
            f"Provider returned an error for the ticker {ticker.upper()}: {chart['error']}"
        )
    result = chart.get("result")
    if not result or not result[0].get("timestamp"):
        raise ValidationError(f"No data found for the ticker {ticker.upper()}")


def parse_chart_to_rows(payload):
    result = payload["chart"]["result"][0]
    gmtoffset = result["meta"].get("gmtoffset", 0)
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]

    rows = []
    for ts, open_, high, low, close, volume in zip(
        timestamps,
        quote["open"],
        quote["high"],
        quote["low"],
        quote["close"],
        quote["volume"],
    ):
        if None in (open_, high, low, close, volume):
            continue
        trading_date = datetime.datetime.fromtimestamp(
            ts + gmtoffset, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d")
        rows.append((trading_date, open_, high, low, close, volume))

    return rows


def build_csv(payload):
    rows = parse_chart_to_rows(payload)
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


def save_data(dated_directory, ticker, data):
    path = pathlib.Path(dated_directory / f"{ticker}.csv")
    path.write_bytes(data)
    logger.info(f"Data has been wrote to {str(path)}")
