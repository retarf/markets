import os
import shutil
import logging

import pandas as pd

from airflow.sdk import dag
from airflow.providers.standard.operators.python import PythonOperator

from snowflake.connector.pandas_tools import write_pandas

from handlers import get_ticker_from_file_name, get_file_list
from connection import connect

from constants import CSV, NEW_DATA_DIR, UPLOADED_DATA_DIR

PARQUET_EXTENSION = "parquet"
RAW_SCHEMA="RAW"
DATA_TABLE = "DATA"
DATE = "DATE"
OPEN = "OPEN"
HIGH = "HIGH"
LOW = "LOW"
CLOSE = "CLOSE"
VOLUME = "VOLUME"
TICKER = "TICKER"
SOURCE_FILE = "SOURCE_FILE"


logger = logging.getLogger()
logger.setLevel(logging.INFO)




def read_csv_to_dataframe(csv_file):
    logger.info(f"Reading csv file {csv_file}")
    parquet_file_path = os.path.join(NEW_DATA_DIR, csv_file)
    return pd.read_csv(parquet_file_path)


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


def add_ticker_column(df, ticker):
    df[TICKER] = ticker
    return df


def add_source_file_column(df, csv_file):
    df[SOURCE_FILE] = csv_file
    return df


def transform_raw_data(df, ticker, csv_file):
    df = rename_column_names(df)
    df = reformat_date_column(df)
    df = add_ticker_column(df, ticker)
    df = add_source_file_column(df, csv_file)
    return df


def write_csv_to_snowflake(csv_file):
    try:
        logger.info(f"Reading csv file {csv_file}")
        ticker = get_ticker_from_file_name(csv_file)
        df = read_csv_to_dataframe(csv_file)
        df = transform_raw_data(df, ticker, csv_file)
        logger.info(f"Writing {ticker} data to snowflake")
        ctx = connect()
        write_pandas(conn=ctx, df=df, table_name=DATA_TABLE, schema=RAW_SCHEMA)
        ctx.close()
        logger.info(f"Data for {ticker} has been written to snowflake")
    except Exception as e:
        logger.error(f'Error occurred during writing {ticker} data to snowflake: {e}')
        raise
    else:
        src = os.path.join(NEW_DATA_DIR, csv_file)
        dst = os.path.join(UPLOADED_DATA_DIR, csv_file)
        shutil.copy(src, dst)
        os.remove(src)
    finally:
        logger.info(f"Moving data operation to snowflake for {ticker} has been completed.")


def load_csv_to_snowflake_operation():
    new_csv_file_list = get_file_list(NEW_DATA_DIR, CSV)
    uploaded_csv_file_list = get_file_list(UPLOADED_DATA_DIR, CSV)
    csv_file_list = set(new_csv_file_list).symmetric_difference(uploaded_csv_file_list)
    for csv_file in csv_file_list:
        write_csv_to_snowflake(csv_file)


@dag(dag_id="load_csv_to_snowflake_dag")
def load_csv_to_snowflake_dag():
        PythonOperator(
            task_id="load_csv_to_snowflake_operation",
            python_callable=load_csv_to_snowflake_operation,
        )


load_csv_to_snowflake_dag()
