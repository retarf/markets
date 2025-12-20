from airflow.sdk import dag
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.state import DagRunState


@dag()
def master_load_data_to_snowflake_dag():
    pull_stock_data_dag = TriggerDagRunOperator(
        task_id="run_pull_stock_data_dag",
        trigger_dag_id="pull_stock_data_dag",
        wait_for_completion=True,
        allowed_states=[DagRunState.FAILED, DagRunState.SUCCESS],
        poke_interval=15
    )
    load_csv_to_snowflake_dag = TriggerDagRunOperator(
        task_id="run_load_csv_to_snowflake_dag",
        trigger_dag_id="load_csv_to_snowflake_dag"
    )

    pull_stock_data_dag >> load_csv_to_snowflake_dag


master_load_data_to_snowflake_dag()
