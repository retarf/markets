import os
import logging
from airflow.sdk import dag
from airflow.providers.standard.operators.python import PythonOperator

from handlers.aws import get_aws_session
from handlers.redshift import execute


PARQUET_EXTENSION = "parquet"

BUCKET_NAME = 's3-markets'
RAW_DATA_DIR = "raw"

S3_NAME = 's3'

IAM_ROLE = os.environ['AWS_IAM_ROLE']
REDSHIFT_DB = os.environ['AWS_REDSHIFT_DB']
REDSHIFT_SCHEMA = 'public'

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_object_list():
    session = get_aws_session()
    client = session.client(S3_NAME)
    response = client.list_objects_v2(Bucket=BUCKET_NAME)
    result = response.get('Contents', [])
    return [i['Key'] for i in result]

def create_table(ticker):
    sql = (
        f"CREATE TABLE IF NOT EXISTS {ticker} (Data date, Otwarcie double precision, Najwyzszy double precision, "
        f"Najnizszy double precision, Zamkniecie double precision, Wolumen double precision);"
    )
    return execute(sql)

def copy_data(ticker, object_path):
    sql = f"COPY {REDSHIFT_DB}.{REDSHIFT_SCHEMA}.{ticker} FROM '{object_path}' IAM_ROLE '{IAM_ROLE}' FORMAT AS PARQUET;"
    return execute(sql)


def copy_s3_to_redshift_operation(obj):
    object_path = f"s3://{BUCKET_NAME}/{obj}"
    ticker = obj.strip(f"{RAW_DATA_DIR}/").strip(f".{PARQUET_EXTENSION}")
    create_table(ticker)
    result = copy_data(ticker, object_path)
    logger.info(f"Copy operation has been executed.")
    logger.info(f"Result: {result}")


@dag(dag_id="copy_s3_to_redshift_dag")
def copy_s3_to_redshift_dag():
    for obj in get_object_list():
        obj_name = obj.split("/")[1]
        PythonOperator(
            task_id=f"{obj_name}_copy_s3_to_redshift_operation",
            python_callable=copy_s3_to_redshift_operation,
            op_kwargs={'obj': obj}
        )


copy_s3_to_redshift_dag()
