import logging

from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lit, to_date
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


def read_csv_to_dataframe(csv_file_path):
    return spark.read.schema(input_schema).option("header", True).option("dateFormat", PYSPARK_DATE_FORMAT).csv(csv_file_path)


def get_ticker_from_path(file_path):
    return Path(file_path).name.split('.')[0].upper()


def get_ds_from_path(file_path):
    return Path(file_path).parent.name.split('=')[1]


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
    return df.select(col(Column.date)).orderBy(col(Column.date), ascending=False).limit(1)


def get_recent_data(df, last_data_date, ds) -> DataFrame:
    return df.filter( (col(Column.date) > last_data_date) & (col(Column.date) < ds) )


def save_data(df) -> None:
    save_table(df, RAW_STOCK_DATA)


def add_ticker_column(df, ticker):
    return df.withColumn(Column.ticker, lit(ticker)) \
             .select(
                Column.ticker, 
                Column.date, 
                Column.open, 
                Column.high, 
                Column.low,
                Column.close,
                Column.volume
            )


def save_last_data_date_in_metastore(last_date_df) -> None:
    save_table(last_date_df, METASTORE__LAST_DATA)
    logger.info("Data has been saved to the warehouse.")
