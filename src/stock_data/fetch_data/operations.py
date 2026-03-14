import os
import json
import pathlib

import requests
import logging

from stock_data import DATALAKE


TICKER_LIST = ['xtb', "orl"]

NO_DATA_ROW = b"Brak danych"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ValidationError(ValueError):
    pass


def validate_data(ticker, data):
    if data[:11] == NO_DATA_ROW:
        raise ValidationError(f"No data found for the ticker {ticker.upper()}")


def fetch_data(ticker):
    data_url = os.environ.get("DATA_SOURCE_URI")
    response = requests.get(data_url.format(ticker=ticker), timeout=30)  # requests.exceptions.Timeout or ReadTimeout
    response.raise_for_status()  # HTTPError
    return response.content


def create_dated_directory(date_string: str) -> pathlib.Path:
    custom_path = f"{DATALAKE}/dt={date_string}"
    path = pathlib.Path(custom_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_data(dated_directory, ticker, data):
    path = pathlib.Path(dated_directory / f"{ticker.lower()}.csv")
    path.write_bytes(data)
    logger.info(f"Data has been wrote to {str(path)}")

