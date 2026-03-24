#!/usr/bin/env python

import sys
import logging

import click

from stock_data import spark
from stock_data.load_data import METASTORE__LAST_DATA


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


from warehouse.snowflake.table import load_table, save_table
from operations import (
    get_ticker_from_path,
    get_ds_from_path,
    get_last_data_date_from_metastore,
    extract_all_data_from_csv,
    select_incremental_data,
    perform_quality_checks,
    get_current_last_date_dataframe,
    add_ticker_column,
    add_source_path_column,
    add_load_ts_column,
    reorder_columns,
    load_incremental_data,
    save_last_data_date_in_metastore
)


@click.command()
@click.option("--path", help="path to a data file.")
def run(path: str) -> None:

    logger.info(f"Starting to load data from path {path} to snowflake")

    ticker = get_ticker_from_path(path)
    end_date = get_ds_from_path(path)

    # Get last trading date from metastore
    metastore = load_table(spark, METASTORE__LAST_DATA)
    start_date = get_last_data_date_from_metastore(metastore, ticker, end_date)

    # Extract incremental data since the last loaded trading date
    all_data = extract_all_data_from_csv(path)
    new_data = select_incremental_data(all_data, start_date, end_date)

    # Perform quality checks
    new_data = perform_quality_checks(new_data)

    # Transform
    new_data = add_ticker_column(new_data, ticker)
    new_data = add_source_path_column(new_data, path)
    new_data = add_load_ts_column(new_data, path)
    new_data = reorder_columns(new_data)

    # Load incremental data to warehouse data table
    load_incremental_data(new_data)

    # Save last trading date to metastore
    current_last_date_dataframe = get_current_last_date_dataframe(new_data)
    save_last_data_date_in_metastore(current_last_date_dataframe)

    logger.info("Data has been successfully loaded.")



if __name__ == '__main__':
    run()