import sys
import logging

import click

from stock_data.fetch_data.operations import (
    validate_data,
    fetch_data,
    build_csv,
    create_dated_directory,
    save_data,
)


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@click.command
@click.option("--date", help="Date when data has been fetched.")
@click.option("--ticker", help="Stock ticker.")
def run(date: str, ticker: str) -> None:
    logger.info(f"Starting fetch data operation for date {date} ticker {ticker}")
    payload = fetch_data(ticker)
    validate_data(ticker, payload)
    data = build_csv(payload)
    dated_directory = create_dated_directory(date)
    save_data(dated_directory, ticker, data)
    logger.info(f"Data has been downloaded for the ticker {ticker.upper()} for date: {date}")


if __name__ == "__main__":
    run()