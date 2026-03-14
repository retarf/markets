from airflow.providers.docker.operators.docker import DockerOperator

from stock_data.variables import variables
from stock_data.mounts import src, datalake



class PysparkOperator(DockerOperator):

    def __init__(self, task_id: str, command: str, **kwargs):
        super().__init__(
            task_id=task_id, 
            command=command, 
            image="markets-pyspark:latest",
            docker_url="unix://var/run/docker.sock",
            environment=variables,
            mounts=[src, datalake],
            mount_tmp_dir=False,
            auto_remove="success",
            **kwargs
        )