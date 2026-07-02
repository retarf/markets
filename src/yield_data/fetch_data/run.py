import sys
import logging

import click

from yield_data.fetch_data.operations import (
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
@click.option("--date", help="Capture date the data is landed under (YYYY-MM-DD).")
@click.option("--year", help="Calendar year of the Treasury yield curve to fetch.")
def run(date: str, year: str) -> None:
    logger.info(f"Starting fetch yield data operation for year {year}")
    payload = fetch_data(year)
    validate_data(year, payload)
    data = build_csv(payload)
    dated_directory = create_dated_directory(date)
    save_data(dated_directory, data)
    logger.info(f"Treasury yield curve for year {year} landed under dt={date}")


if __name__ == "__main__":
    run()
