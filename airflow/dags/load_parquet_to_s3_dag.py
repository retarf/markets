import os
import logging
import polars as pl
from airflow.sdk import dag
from airflow.providers.standard.operators.python import PythonOperator

from handlers.operations import get_ticker_from_file_name, get_file_list
from handlers.aws import get_aws_session


INPUT_DIR = "/project/datalake"
S3_DIR = "/project/s3"
PARQUET_EXTENSION = "parquet"
ROWS_LIMIT = 100
BUCKET_NAME = 's3-markets'
RAW_DATA_DIR = "raw"

logger = logging.getLogger()
logger.setLevel(logging.INFO)



parquet_file_list = get_file_list(INPUT_DIR, PARQUET_EXTENSION)


def read_parquet_to_dataframe(parquet_file_path):
    logger.info(f"Reading parquet file {parquet_file_path}")
    return pl.read_parquet(parquet_file_path)


def limit_number_of_rows(dataframe, number_of_rows):
    logger.info(f"Limiting number of rows to {dataframe.shape[0]}")
    return dataframe.sort('Data', descending=True).limit(number_of_rows).sort('Data')


def write_dataframe_to_parquet(ticker, dataframe):
    path = os.path.join(f"{S3_DIR}", f"{ticker}.{PARQUET_EXTENSION}")
    dataframe.write_parquet(file=path, compression='uncompressed')
    logger.info(f"Successfully wrote parquet to {path}.")


def limit_number_of_rows_operation(ticker, parquet_file):
    parquet_file_path = os.path.join(INPUT_DIR, parquet_file)
    dataframe = read_parquet_to_dataframe(parquet_file_path)
    dataframe = limit_number_of_rows(dataframe, ROWS_LIMIT)
    write_dataframe_to_parquet(ticker, dataframe)


def write_to_s3_operation(ticker):
    parquet_file_name = f"{ticker}.{PARQUET_EXTENSION}"
    parquet_file = os.path.join(f"{S3_DIR}", parquet_file_name)
    session = get_aws_session()
    s3_client = session.client('s3')
    s3_file_path = f"{RAW_DATA_DIR}/{parquet_file_name}"
    s3_client.upload_file(
        parquet_file,
        BUCKET_NAME,
        s3_file_path
    )
    logger.info(f"File {parquet_file_name} has been successfully uploaded to s3.")



@dag(dag_id="load_parquet_to_s3_dag")
def load_parquet_to_s3_dag():
    for parquet_file in parquet_file_list:
        ticker = get_ticker_from_file_name(parquet_file)
        limit_number_of_rows = PythonOperator(
            task_id=f"{ticker.upper()}_limit_number_of_rows_operation",
            python_callable=limit_number_of_rows_operation,
            op_kwargs={'ticker': ticker, 'parquet_file': parquet_file}
        )
        write_to_s3 = PythonOperator(
            task_id=f"{ticker.upper()}_write_to_s3",
            python_callable=write_to_s3_operation,
            op_kwargs={'ticker': ticker}
        )
        limit_number_of_rows >> write_to_s3


load_parquet_to_s3_dag()
