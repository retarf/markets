import os
import logging
import polars as pl
from airflow.sdk import dag
from airflow.providers.standard.operators.python import PythonOperator

from constants import CSV, UPLOADED_DATA_DIR, RAW_COLUMN
from handlers import get_ticker_from_file_name, get_file_list, get_latest_file_list



DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_ENGINE = 'postgresql'
TABLE_NAME = 'raw_stock_data'

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def read_csv_to_dataframe(csv_file_path):
    logger.info(f"Reading csv file {csv_file_path}")
    df = pl.read_csv(csv_file_path)
    logger.info(f"{df.select(pl.len()).item(0,0)} rows has been read.")
    return df


def write_dataframe_to_database(ticker, df):
    uri = f'{DB_ENGINE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    logger.info(f"Writing dataframe to {ticker} table.")
    result = df.write_database(
        table_name=TABLE_NAME,
        connection=uri,
        if_table_exists='append'
    )
    if result == -1:
        logger.error(f"Failed to write dataframe to {ticker} table.")
    else:
        logger.info(f"{df.select(pl.len()).item(0,0)} rows has been written.")
        logger.info(f"Successfully wrote dataframe to {ticker} table with {result} rows.")


def get_latest_csv_file_list():
    csv_file_list = get_file_list(UPLOADED_DATA_DIR, CSV)
    return get_latest_file_list(csv_file_list)


def rename_column_names(df):
    return df.rename(
        {
            RAW_COLUMN.DATE: "trading_date",
            RAW_COLUMN.OPEN: "open",
            RAW_COLUMN.HIGH: "high",
            RAW_COLUMN.LOW: "low",
            RAW_COLUMN.CLOSE: "close",
            RAW_COLUMN.VOLUME: "volume",
        }
    )

def add_ticker_column(df, ticker):
    df = df.with_columns(pl.lit(ticker).alias("ticker"))
    return df


def add_source_file_column(df, csv_file):
    df = df.with_columns(pl.lit(csv_file).alias("source_file"))
    return df


def transform_raw_data(df, ticker, csv_file):
    df = rename_column_names(df)
    df = add_ticker_column(df, ticker)
    df = add_source_file_column(df, csv_file)
    return df


def load_csv_to_database_operation():
    for csv_file in get_latest_csv_file_list():
        ticker = get_ticker_from_file_name(csv_file)
        csv_file_path = os.path.join(UPLOADED_DATA_DIR, csv_file)
        df = read_csv_to_dataframe(csv_file_path)
        df = transform_raw_data(df, ticker, csv_file)
        write_dataframe_to_database(ticker, df)


@dag(dag_id="load_csv_to_database_dag")
def load_csv_to_database_dag():
        PythonOperator(
            task_id="load_csv_to_database_operation",
            python_callable=load_csv_to_database_operation,
        )


load_csv_to_database_dag()
