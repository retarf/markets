import os
import logging
import polars as pl
from airflow.sdk import dag
from airflow.providers.standard.operators.python import PythonOperator

from handlers.operations import get_ticker_from_file_name, get_file_list


INPUT_DIR = "/project/datalake"
PARQUET_EXTENSION = "parquet"
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_ENGINE = 'postgresql'

logger = logging.getLogger()
logger.setLevel(logging.INFO)



parquet_file_list = get_file_list(INPUT_DIR, PARQUET_EXTENSION)


def read_parquet_to_dataframe(parquet_file_path):
    logger.info(f"Reading parquet file {parquet_file_path}")
    return pl.read_parquet(parquet_file_path)


def write_dataframe_to_database(ticker, dataframe):
    uri = f'{DB_ENGINE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    logger.info(f"Writing dataframe to {ticker} table.")
    result = dataframe.write_database(
        table_name=ticker,
        connection=uri,
        if_table_exists='replace'
    )
    if result == -1:
        logger.error(f"Failed to write dataframe to {ticker} table.")
    else:
        logger.info(f"Successfully wrote dataframe to {ticker} table with {result} rows.")


def load_parquet_to_database_operation(ticker, parquet_file):
    parquet_file_path = os.path.join(INPUT_DIR, parquet_file)
    dataframe = read_parquet_to_dataframe(parquet_file_path)
    write_dataframe_to_database(ticker, dataframe)


@dag(dag_id="load_parquet_to_database_dag")
def load_parquet_to_database_dag():
    for parquet_file in parquet_file_list:
        ticker = get_ticker_from_file_name(parquet_file)
        PythonOperator(
            task_id=f"{ticker.upper()}_load_parquet_to_database_operation",
            python_callable=load_parquet_to_database_operation,
            op_kwargs={'ticker': ticker, 'parquet_file': parquet_file}
        )


load_parquet_to_database_dag()
