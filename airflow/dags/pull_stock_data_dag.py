import os
from airflow.sdk import dag
from airflow.providers.standard.operators.python import PythonOperator

import requests
import logging

TICKER_LIST = ['xtb', "orl"]
DATA_DIR = "/project/datalake"

NO_DATA_ROW = b"Brak danych"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

data_url = os.environ.get("DATA_SOURCE_URI")


class ValidationError(ValueError):
    pass


def validate_data(ticker, data):
    if data[:11] == NO_DATA_ROW:
        raise ValidationError(f"No data found for the ticker {ticker.upper()}")


def pull_data(ticker):
    return requests.get(data_url.format(ticker=ticker)).content


def save_data(ticker, data):
    with open(f"{DATA_DIR}/{ticker}.csv", 'wb+') as f:
        f.write(data)

    logger.info(f"Data has been downloaded for the ticker {ticker.upper()}.")


def pull_stock_data_operation(ticker):
    data = pull_data(ticker)
    validate_data(ticker, data)
    save_data(ticker, data)


@dag(dag_id="pull_stock_data_dag")
def pull_stock_data_dag():
    for ticker in TICKER_LIST:
        PythonOperator(task_id=f"{ticker.upper()}_pull_stock_data_operation", python_callable=pull_stock_data_operation, op_kwargs={'ticker': ticker})

pull_stock_data_dag()
