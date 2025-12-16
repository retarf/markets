import os
import logging

import pandas as pd

from airflow.sdk import dag
from airflow.providers.standard.operators.python import PythonOperator

from snowflake.connector.pandas_tools import write_pandas

from handlers.operations import get_ticker_from_file_name, get_file_list
from handlers.connection import connect


INPUT_DIR = "/project/datalake"
PARQUET_EXTENSION = "parquet"
RAW_SCHEMA="RAW"
DATE = "DATE"
OPEN = "OPEN"
HIGH = "HIGH"
LOW = "LOW"
CLOSE = "CLOSE"
VOLUME = "VOLUME"


logger = logging.getLogger()
logger.setLevel(logging.INFO)


parquet_file_list = get_file_list(INPUT_DIR, PARQUET_EXTENSION)


def read_parquet_to_dataframe(parquet_file):
    logger.info(f"Reading parquet file {parquet_file}")
    parquet_file_path = os.path.join(INPUT_DIR, parquet_file)
    return pd.read_parquet(parquet_file_path)


def rename_column_names(df):
    return df.rename(
        columns={
            "Data": DATE,
            "Otwarcie": OPEN,
            "Najwyzszy": HIGH,
            "Najnizszy": LOW,
            "Zamkniecie": CLOSE,
            "Wolumen": VOLUME
        }
    )


def reformat_date_column(df):
    df[DATE] = pd.to_datetime(df[DATE], errors='coerce').dt.date
    return df


def create_table(ticker, cursor):
    upper_ticker = ticker.upper()
    logger.info(f"Creating table {upper_ticker}.")
    cursor.execute(
        (
            f"CREATE TABLE IF NOT EXISTS {RAW_SCHEMA}.{upper_ticker} "
            f"({DATE} DATE, "
            f"{OPEN} double precision, "
            f"{HIGH} double precision, "
            f"{LOW} double precision, "
            f"{CLOSE} double precision, "
            f"{VOLUME} double precision);"
        )
    )
    logger.info(f"Table {upper_ticker} has been created.")


def load_parquet_to_snowflake_operation(ticker, parquet_file):
    df = read_parquet_to_dataframe(parquet_file)
    df = rename_column_names(df)
    df = reformat_date_column(df)
    ctx = connect()
    cursor = ctx.cursor()
    create_table(ticker, cursor)
    write_pandas(conn=ctx, df=df, table_name=ticker.upper(), schema=RAW_SCHEMA)
    ctx.close()


@dag(dag_id="load_parquet_to_snowflake_dag")
def load_parquet_to_snowflake_dag():
    for parquet_file in parquet_file_list:
        ticker = get_ticker_from_file_name(parquet_file)
        PythonOperator(
            task_id=f"{ticker.upper()}_load_parquet_to_snowflake_operation",
            python_callable=load_parquet_to_snowflake_operation,
            op_kwargs={'ticker': ticker, 'parquet_file': parquet_file}
        )


load_parquet_to_snowflake_dag()
