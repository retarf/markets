import os
from pyspark.sql import SparkSession
import snowflake.connector as sc

SNOWFLAKE_SOURCE_NAME = "net.snowflake.spark.snowflake"

params = {
    'account': os.environ.get('SNOWFLAKE_ACCOUNT'),
    'user': os.environ.get('SNOWFLAKE_USER'),
    'authenticator': 'SNOWFLAKE_JWT',
    'private_key_file': os.environ.get('SNOWFLAKE_PRIVATE_KEY_FILE'),
    'private_key_file_pwd': os.environ.get('SNOWFLAKE_PRIVATE_KEY_FILE_PWD'),
    'warehouse': os.environ.get('SNOWFLAKE_WAREHOUSE'),
    'database': os.environ.get('SNOWFLAKE_DATABASE'),
    'schema': os.environ.get('SNOWFLAKE_SCHEMA')
}

def connect():
    return sc.connect(**params)


def fetch_dataframe(table_name):
    spark = SparkSession.builder.getOrCreate()
    df = spark.read.format(SNOWFLAKE_SOURCE_NAME).options(**params).option("dbtable", table_name).load()

    return df