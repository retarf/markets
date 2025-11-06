from airflow.sdk import dag
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.state import DagRunState


@dag()
def master_load_data_dag():
    pull_stock_data_dag = TriggerDagRunOperator(
        task_id="run_pull_stock_data_dag",
        trigger_dag_id="pull_stock_data_dag",
        wait_for_completion=True,
        allowed_states=[DagRunState.FAILED, DagRunState.SUCCESS],
        poke_interval=15
    )
    reformat_to_parquet_dag = TriggerDagRunOperator(
        task_id="run_reformat_to_parquet_dag",
        trigger_dag_id="reformat_to_parquet_dag",
        wait_for_completion=True,
        allowed_states=[DagRunState.SUCCESS],
        poke_interval=10
    )
    load_data_dag = TriggerDagRunOperator(
        task_id="run_load_parquet_to_database_dag",
        trigger_dag_id="load_parquet_to_database_dag"
    )

    pull_stock_data_dag >> reformat_to_parquet_dag >> load_data_dag


master_load_data_dag()
