import logging

from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lit, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DateType, DoubleType

from warehouse.snowflake.table import load_table, save_table
from stock_data import spark, Column, PYSPARK_DATE_FORMAT, input_schema, RAW_STOCK_DATA
from stock_data.load_data import METASTORE__LAST_DATA
from stock_data.load_data.quality_checks import (
    not_null_quality_check,
    greater_than_zero_quality_check,
    low_greater_than_high_quality_check
)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def extract_all_data_from_csv(csv_file_path):
    logger.info(f"Reading file on path: {csv_file_path}")
    return spark.read.schema(input_schema).option("header", True).option("dateFormat", PYSPARK_DATE_FORMAT).csv(csv_file_path)


def get_ticker_from_path(path):
    return Path(path).name.split('.')[0].upper()


def get_ds_from_path(path):
    return Path(path).parent.name.split('=')[1]


def perform_quality_checks(df) -> DataFrame:
    not_null_quality_check(df)
    greater_than_zero_quality_check(df)
    low_greater_than_high_quality_check(df)
    return df


def get_last_data_date_from_metastore(metastore, ticker, ds) -> str | None:
    row = metastore.filter( (col(Column.ticker) == ticker) & (col(Column.date) < ds) )\
                    .select(col(Column.date)) \
                    .orderBy(col(Column.date).desc()) \
                    .first()
    
    return row[Column.date] if row else None


def get_current_last_date_dataframe(df) -> DataFrame:
    return df.select(col(Column.ticker), col(Column.date)).orderBy(col(Column.date), ascending=False).limit(1)


def select_incremental_data(all_data, start_date: str, end_date: str) -> DataFrame:
    """Filter only data between the start_date and the end_date

    :param all_data: Dataframe with all data to filter
    :type all_data: DataFrame
    :param start_date: The start data used in filter. 
        Only data with transaction date grather than start_date are included.
    :type start_date: str
    :param end_date: The end data used in filter
    :type end_date: str
    :returns: The new dataframe 
    "rtype: DataFrame
    """

    if start_date:
        logger.info(f"Filtering data from {start_date} to {end_date} to load.")
        new_data = all_data.filter( (col(Column.date) > start_date) & (col(Column.date) < end_date) )
    else:
        logger.warning(f"All data will be loaded.")
        new_data = all_data
    
    return new_data


def load_incremental_data(df) -> None:
    save_table(df, RAW_STOCK_DATA)


def add_ticker_column(df, ticker):
    return df.withColumn(Column.ticker, lit(ticker))


def add_source_path_column(df, source_path):
    return df.withColumn(Column.source_path, lit(source_path))


def add_load_ts_column(df, load_ts):
    return df.withColumn(Column.load_ts, current_timestamp())


def reorder_columns(df):
    return df.select(
        Column.ticker, 
        Column.date, 
        Column.open, 
        Column.high, 
        Column.low,
        Column.close,
        Column.volume,
        Column.source_path,
        Column.load_ts
    )


def save_last_data_date_in_metastore(last_date_df) -> None:
    save_table(last_date_df, METASTORE__LAST_DATA)
    logger.info(f"Data has been saved to the table: {METASTORE__LAST_DATA}.")
