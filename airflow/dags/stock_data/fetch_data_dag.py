import datetime

from pathlib import Path

from airflow.sdk import dag, task, get_current_context, Asset

from airflow.src.stock_data.assets import data_fetched
from stock_data import DATALAKE
from stock_data.fetch_data.operations import fetch_stock_data_operation
from stock_data.fetch_data import TICKER_LIST



@dag(
    start_date=datetime.datetime(2026, 3, 5),
    schedule="@daily",
    catchup=False,
)
def fetch_data_dag():

    @task(
            outlets=[data_fetched]
    )
    def fetch_stock_data_task(ticker: str, outlet_events):
        ds = get_current_context()["ds"]
        fetch_stock_data_operation(ticker, ds)
        path = f'{DATALAKE}/dt={{ ds }}/{ticker}.csv'
        outlet_events[data_fetched].add(Asset(path))

    fetch_stock_data_task.expand(ticker=TICKER_LIST)


dag = fetch_stock_data_dag()