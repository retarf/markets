#!/usr/bin/env python
import click

from stock_data import spark
from stock_data.load_data import METASTORE__LAST_DATA

from warehouse.snowflake.table import load_table, save_table
from operations import (
    get_ticker_from_path,
    get_ds_from_path,
    get_last_data_date_from_metastore,
    read_csv_to_dataframe,
    get_recent_data,
    perform_quality_checks,
    get_current_last_date_dataframe,
    add_ticker_column,
    save_data,
    save_last_data_date_in_metastore
)


@click.command()
@click.option("--path", help="path to a data file")
def run(path: str) -> None:
    ticker = get_ticker_from_path(path)
    ds = get_ds_from_path(path)
    metastore = load_table(spark, METASTORE__LAST_DATA)
    metastore_last_data_date = get_last_data_date_from_metastore(metastore, ticker, ds)
    all_data = read_csv_to_dataframe(path)
    recent_data = get_recent_data(all_data, metastore_last_data_date, ds)
    recent_data = perform_quality_checks(recent_data)
    current_last_date_dataframe = get_current_last_date_dataframe(recent_data)
    recent_data = add_ticker_column(recent_data, ticker)
    save_data(recent_data)
    save_last_data_date_in_metastore(current_last_date_dataframe)



if __name__ == '__main__':
    run()