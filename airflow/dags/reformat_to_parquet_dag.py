import os
import logging
from airflow.sdk import dag
from airflow.providers.standard.operators.python import PythonOperator
from pyarrow import csv, parquet


INPUT_DIR = "/project/datalake"
OUTPUT_DIR = "/project/datalake"
CSV_EXTENSION = "csv"
PARQUET_EXTENSION = "parquet"


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_csv_file_generator():
    return (file for file in os.listdir(INPUT_DIR) if file.split(".")[-1] == CSV_EXTENSION)


def get_ticker_from_file_name(file_name):
    return file_name.split(".")[0]


def reformat_csv_to_parquet_operation(ticker, csv_file):
    table = csv.read_csv(f"{INPUT_DIR}/{csv_file}")
    output_path = f"{OUTPUT_DIR}/{ticker}.{PARQUET_EXTENSION}"
    parquet.write_table(table, output_path)
    logger.info(f"Wrote {csv_file} to {output_path}")


@dag()
def reformat_csv_to_parquet_dag():
    for csv_file in get_csv_file_generator():
        ticker = get_ticker_from_file_name(csv_file)
        PythonOperator(
            task_id=f"{ticker.upper()}_reformat_csv_to_parquet_operation",
            python_callable=reformat_csv_to_parquet_operation,
            op_kwargs={'ticker': ticker, 'csv_file': csv_file}
        )


reformat_csv_to_parquet_dag()