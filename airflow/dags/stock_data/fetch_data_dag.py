import datetime

from airflow.sdk import dag, task, get_current_context

from assets import datalake_asset
from stock_data.fetch_data.operations import fetch_stock_data_operation
from stock_data.fetch_data import TICKER_LIST


@dag(
    start_date=datetime.datetime(2026, 3, 5),
    schedule="@daily",
    catchup=False,
)
def fetch_stock_data_dag():

    @task
    def fetch_stock_data_task(ticker: str):
        ctx = get_current_context()
        ds = ctx["ds"]
        fetch_stock_data_operation(ticker, ds)
    
    @task(outlets=[datalake_asset])
    def mark_done():
        return "done"
    
    fetched = fetch_stock_data_task.expand(ticker=TICKER_LIST)
    done = mark_done()

    fetched >> done

dag = fetch_stock_data_dag()