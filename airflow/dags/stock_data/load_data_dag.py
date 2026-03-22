import logging

from datetime import datetime

from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.sdk import dag, task, get_current_context

from stock_data.assets import data_fetched
from stock_data.operators import PysparkOperator


logger = logging.getLogger()
# logger.setLevel(logging.INFO)



# @task
# def get_path_from_event():
#     context = get_current_context()
#     logger.warning(context)
#     events = context['triggering_asset_events'][data_fetched]
#     logger.warning(events)
#     return events[-1].uri.replace("file://", "")


@dag(
    schedule=[data_fetched],
    start_date=datetime(2026, 1, 1),
    catchup=False
)
def load_data_dag():

    # asset_path = "{{ (triggering_asset_events[data_fetched] | first).uri }}"
    #asset_path = "{{ (triggering_asset_events.values() | first).uri }}"

    @task(inlets=[data_fetched])
    def get_path(*, inlet_events):
        # ctx = get_current_context()
        uri = inlet_events[-1][0].asset.uri
        # ctx["params"]["path"] = uri.replace("file://", "")
        return uri.replace("file://", "")

    path_arg = get_path()

    load_data_run = PysparkOperator(
        task_id="load_data",
        # command=f"python /project/src/stock_data/load_data/run.py --path {{ params.path }}",
        #command=f"python /project/src/stock_data/load_data/run.py --path {{ ti.xcom_pull(task_ids='get_path') }}",
        command=f"python /project/src/stock_data/load_data/run.py --path {{ tasks.get_path.output }}",
    )

    path_arg >> load_data_run
    
    
dag = load_data_dag()
        