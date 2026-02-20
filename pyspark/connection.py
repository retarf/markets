import os
from pyspark.sql import SparkSession
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import re

SNOWFLAKE_SOURCE_NAME = "net.snowflake.spark.snowflake"
SNOWFLAKE_JDBC_DRIVER="/project/pyspark/libs/snowflake-jdbc-3.28.0.jar"
SNOWFLAKE_CONNECTOR="/project/pyspark/libs/spark-snowflake_2.13-3.1.7.jar"
JARS_LIST = [SNOWFLAKE_JDBC_DRIVER, SNOWFLAKE_CONNECTOR]
JARS = ','.join(JARS_LIST)

def get_private_key():
    key_path = os.environ.get('PYSPARK_PRIVATE_KEY_FILE')
    with open(key_path, "rb") as key_file:
        p_key = serialization.load_pem_private_key(
            key_file.read(),
            password = os.environ.get('PYSPARK_PRIVATE_KEY_FILE_PWD').encode(),
            backend = default_backend()
        )
        pkb = p_key.private_bytes(
            encoding = serialization.Encoding.PEM,
            format = serialization.PrivateFormat.PKCS8,
            encryption_algorithm = serialization.NoEncryption()
        )
        pkb = pkb.decode("UTF-8")
        return re.sub("-*(BEGIN|END) PRIVATE KEY-*\n","",pkb).replace("\n","")


sfOptions = {
    'sfURL': f'{os.environ.get('SNOWFLAKE_ACCOUNT')}.snowflakecomputing.com',
    'sfUser': os.environ.get('PYSPARK_USER'),
    "pem_private_key": get_private_key(),
    'sfSchema': os.environ.get('SNOWFLAKE_SCHEMA'),
    'sfDatabase': os.environ.get('SNOWFLAKE_DATABASE'),
    'sfWarehouse': os.environ.get('SNOWFLAKE_WAREHOUSE'),
}


def get_spark_session():
    return SparkSession.builder \
        .config("spark.jars", JARS) \
        .getOrCreate()
