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


from airflow.sdk import AssetAlias, Asset, get_current_context


test_asset = Asset(name="test_asset", uri="file:///test_asset.txt")
test_asset_alias = AssetAlias("test_asset_alias")


@dag(
    start_date=datetime(2026, 1, 1),
)
def first():

    @task(outlets=[test_asset_alias])
    def emit_event(file, *, outlet_events):
        outlet_events[test_asset_alias].add(
            Asset(name="file", uri=f"file:///{file}")
        )

    first_task = PysparkOperator(
        task_id="first_task",
        command=f"echo {"test first"}"
    )

    first_task >> emit_event("test-{{ ts }}.csv")


@dag(
    schedule=[test_asset_alias],
    start_date=datetime(2026, 1, 1),
)
def second():

    @task(inlets=[test_asset_alias])
    def consume_events(*, inlet_events):
        events = inlet_events[test_asset_alias]
        uri = events[-1].asset.uri.replace("file://", "")
        # ctx = get_current_context()
        # ctx["params"]["uri"] = uri
        print(uri)
        return uri

    # @task(inlets=[test_asset_alias])
    # def build_command(*, inlet_events):
    #     events = inlet_events[test_asset_alias]
    #     uri = events[-1].asset.uri.replace("file://", "")
    #     return f"echo {uri}"

    uri = consume_events()

    second_task = PysparkOperator(
        task_id="first_task",
        #command=f"echo {"test second"} - {{params.uri}}"
        inlets=[test_asset_alias],
        command=f"echo { uri }"
    )

    uri >> second_task


first()
second()