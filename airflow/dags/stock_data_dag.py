
import datetime

from airflow.sdk import dag, task

from stock_data.operators import PysparkOperator
from stock_data.constants import TICKER_LIST


#TICKER_LIST = ["xtb", "orl", "pzu"]


@dag(
    start_date=datetime.datetime(2026, 3, 5),
    schedule="@daily",
    catchup=False,
)
def stock_data_dag():

    @task
    def get_file_params(ticker, ds):
        path = f"/project/datalake/STOCK_DATA/dt={ ds }/{ ticker }.csv"
        return {"path": path, "ticker": ticker, "ds": ds}

    fetch_data_run = PysparkOperator.partial(
        task_id="fetch_data",
        command="python /project/src/stock_data/fetch_data/run.py --date {{ ds }} --ticker {{ params.ticker }}",
    )

    load_data_run = PysparkOperator.partial(
        task_id="load_data",
        command='python /project/src/stock_data/load_data/run.py --path "{{ params.path }}"',
    )

    params = get_file_params.expand(ticker=TICKER_LIST)
    fetch_data_run.expand(params=params)
    load_data_run.expand(params=params)


stock_data_dag()