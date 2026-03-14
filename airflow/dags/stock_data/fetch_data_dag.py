import logging
import datetime

from pathlib import Path

from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import dag, task, get_current_context, Asset

from stock_data.assets import data_fetched
from stock_data.operators import PysparkOperator

TICKER_LIST = ["xtb", "orl", "pzu"]
# TICKER_LIST = ["orl"]


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def attach_asset(context, _):
    ticker = context["params"]["ticker"]
    ds = context["ds"]
    context["outlet_events"][data_fetched].add(
        Asset(f"file:///project/datalake/STOCK_DATA/dt={ds}/{ticker}.csv")
    )


@dag(
    start_date=datetime.datetime(2026, 3, 5),
    schedule="@daily",
    catchup=False,
)
def fetch_data_dag():

    fetch_data_run = PysparkOperator.partial(
        task_id="fetch_data",
        command="python /project/src/stock_data/fetch_data/run.py --date {{ ds }} --ticker {{ params.ticker }}",
        outlets=[data_fetched],
        post_execute=attach_asset,
    ).expand(
        params=[{"ticker": ticker} for ticker in TICKER_LIST]
    )

    fetch_data_run


dag = fetch_data_dag()