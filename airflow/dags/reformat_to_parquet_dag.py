import logging
from airflow.sdk import dag
from airflow.decorators import task
from airflow.providers.standard.operators.python import PythonOperator
from pyarrow import csv, parquet

from handlers.operations import get_ticker_from_file_name, get_file_list


INPUT_DIR = "/project/datalake"
OUTPUT_DIR = "/project/datalake"
CSV_EXTENSION = "csv"
PARQUET_EXTENSION = "parquet"


logger = logging.getLogger()
logger.setLevel(logging.INFO)


csv_file_list = get_file_list(INPUT_DIR, CSV_EXTENSION)


def reformat_csv_to_parquet_operation(ticker, csv_file):
    logger.info(f"Reformatting {ticker} csv file to parquet")
    logger.info(f"Reading {ticker} csv file")
    table = csv.read_csv(f"{INPUT_DIR}/{csv_file}")
    logger.info(f"Writing {ticker} parquet file")
    output_path = f"{OUTPUT_DIR}/{ticker}.{PARQUET_EXTENSION}"
    parquet.write_table(table, output_path)
    logger.info(f"Finished writing {ticker} parquet file")


@dag(dag_id="reformat_to_parquet_dag")
def reformat_csv_to_parquet_dag():
    for csv_file in csv_file_list:
        ticker = get_ticker_from_file_name(csv_file)
        PythonOperator(
            task_id=f"{ticker.upper()}_reformat_csv_to_parquet_operation",
            python_callable=reformat_csv_to_parquet_operation,
            op_kwargs={'ticker': ticker, 'csv_file': csv_file}
        )


reformat_csv_to_parquet_dag()