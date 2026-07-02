import datetime

from airflow.sdk import dag, task

from stock_data.operators import PysparkOperator


# Daily US Treasury yield-curve pull. Mirrors stock_data_dag but for the
# YIELD_DATA (DuckDB) domain: one keyless Treasury request for the current year,
# then a plain-Python DuckDB load — no per-Tenor fan-out, no Spark.
#
# NOTE (dev-verify / infra): the runner image must have `duckdb` installed and the
# `YIELD_WAREHOUSE_DB` env var set (passed via the operator's `environment`). The
# equity `markets-pyspark` image is reused here as a generic container runner; a
# dedicated lightweight yields image is a possible follow-up.
@dag(
    start_date=datetime.datetime(2026, 7, 1),
    schedule="@daily",
    catchup=False,
)
def yield_data_dag():

    @task
    def get_params(ds=None):
        return {
            "year": ds[:4],
            "ds": ds,
            "path": f"/project/datalake/YIELD_DATA/dt={ds}/treasury_yields.csv",
        }

    params = get_params()

    fetch_yields = PysparkOperator(
        task_id="fetch_yields",
        command="python /project/src/yield_data/fetch_data/run.py --date {{ ds }} --year {{ ds[:4] }}",
    )

    load_yields = PysparkOperator(
        task_id="load_yields",
        command='python /project/src/yield_data/load_data/run.py --path "{{ ti.xcom_pull(task_ids=\'get_params\')[\'path\'] }}"',
    )

    params >> fetch_yields >> load_yields


yield_data_dag()
