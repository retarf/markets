from datetime import datetime

from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import dag

from stock_data.assets import data_fetched
from stock_data.mounts import src, datalake


@dag(
    schedule=[data_fetched],
    start_date=datetime(2026, 1, 1),
    catchup=True
)
def load_data_dag():
    pyspark_run = DockerOperator(
        task_id="load_data",
        image="markets-pyspark:latest",
        command="python /project/src/stock_data/load_data/run.py",
        docker_url="unix://var/run/docker.sock",
        environment={"PYTHONPATH": "/project/src"},
        mounts=[src, datalake],
        mount_tmp_dir=False,
        auto_remove="success"
    )

    pyspark_run
    
    
dag = load_data_dag()
        