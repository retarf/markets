import logging

from datetime import datetime

from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.sdk import dag, task, get_current_context

from stock_data.assets import data_fetched
from stock_data.operators import PysparkOperator


logger = logging.getLogger()
logger.setLevel(logging.INFO)


@dag(
    schedule=[data_fetched],
    start_date=datetime(2026, 1, 1),
    catchup=False
)
def load_data_dag():


    @task(inlets=[data_fetched], task_id="get_path")
    def get_path(*, inlet_events):
        events = inlet_events[data_fetched]
        uri = events[-1].asset.uri
        return uri.replace("file://", "")

    load_data_run = PysparkOperator(
        task_id="load_data",
        command="python /project/src/stock_data/load_data/run.py --path {{ ti.xcom_pull(task_ids='get_path') }}",
    )

    file_path = get_path()
    file_path >> load_data_run


dag = load_data_dag()